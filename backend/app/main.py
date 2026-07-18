import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .case_store import get_case, load_cases, public_case
from .config import settings
from .models import CompleteRequest, CreateConsultationRequest, DifferentialsRequest, InvestigationRequest, TurnRequest
from .services import add_evaluator_feedback, add_turn, evaluate, order_investigation, process_voice_turn, store
import httpx

app = FastAPI(title="AI Virtual Patient Simulator", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()], allow_methods=["*"], allow_headers=["*"])


def public_session(session):
    case = get_case(session.case_id)
    return {"id": session.id, "case_id": session.case_id, "status": session.status, "transcript": [turn.model_dump(mode="json") for turn in session.transcript], "ordered_investigation_ids": session.ordered_investigation_ids, "differentials": session.differentials, "investigations": [{"id": item.id, "name": item.name} for item in case.investigations]}


@app.get("/health")
def health(): return {"status": "ok"}


@app.get("/cases")
def list_cases(): return [public_case(case) for case in load_cases().values()]


@app.post("/consultations")
def create_consultation(body: CreateConsultationRequest): return public_session(store.create(body.case_id))


@app.get("/consultations/{consultation_id}")
def get_consultation(consultation_id: str): return public_session(store.get(consultation_id))


@app.websocket("/consultations/{consultation_id}/live")
async def live_dashboard(websocket: WebSocket, consultation_id: str):
    store.get(consultation_id)
    await websocket.accept()
    store.subscribers[consultation_id].add(websocket)
    for event in store.events[consultation_id]:
        await websocket.send_json(event)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        store.subscribers[consultation_id].discard(websocket)


@app.post("/consultations/{consultation_id}/vaani/dispatch")
async def dispatch_vaani_call(consultation_id: str, body: dict):
    session = store.get(consultation_id)
    if not settings.vaani_api_key or not settings.vaani_agent_id:
        raise HTTPException(status_code=503, detail="VAANI_API_KEY and VAANI_AGENT_ID are required")
    contact_number = body.get("contact_number")
    if not contact_number:
        raise HTTPException(status_code=422, detail="contact_number is required in E.164 format")
    payload = {
        "agent_id": settings.vaani_agent_id,
        "contact_number": contact_number,
        "name": "Medical simulation learner",
        "voice": "",
        "metadata": {"consultation_id": session.id, "case_id": session.case_id},
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(f"{settings.vaani_api_base_url.rstrip('/')}/api/trigger-call/", headers={"X-API-Key": settings.vaani_api_key, "Content-Type": "application/json"}, json=payload)
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Vaani dispatch failed: {response.text[:300]}")
    result = response.json()
    output = result.get("output") if isinstance(result.get("output"), dict) else {}
    call_id = result.get("call_id") or result.get("id") or result.get("room_name") or output.get("call_id") or output.get("room_name")
    if not call_id:
        raise HTTPException(status_code=502, detail="Vaani response did not include a call ID")
    store.map_call(session.id, call_id)
    await store.publish(session.id, {"type": "call_status", "status": "dispatching", "call_id": call_id})
    return {"consultation_id": session.id, "call_id": call_id, "status": "dispatching"}


@app.websocket("/vaani/byol/{call_id}")
async def vaani_byol(websocket: WebSocket, call_id: str):
    await websocket.accept()
    await websocket.send_json({"interaction_type": "config", "content": "Server ready"})
    await websocket.send_json({"interaction_type": "greeting", "content": "Hello"})
    # Vaani's dashboard Test Connection has no consultation created in the
    # browser yet. Permit the protocol handshake, but do not expose or mutate
    # any clinical state until a dispatch-created call ID is mapped.
    if call_id not in store.call_to_consultation:
        try:
            while True:
                message = await websocket.receive_json()
                if message.get("response_type") == "ping_pong":
                    await websocket.send_json({"response_type": "ping_pong"})
        except WebSocketDisconnect:
            return
    session = store.by_call(call_id)
    await store.publish(session.id, {"type": "call_status", "status": "active", "call_id": call_id})
    latest_response_id = -1
    pending_task: asyncio.Task | None = None

    async def respond(response_id: int, learner_text: str) -> None:
        reply = await process_voice_turn(session, learner_text)
        chunks = [reply[index:index + 120] for index in range(0, len(reply), 120)] or [""]
        for index, chunk in enumerate(chunks):
            await websocket.send_json({"response_type": "response", "response_id": response_id, "content": chunk, "content_complete": index == len(chunks) - 1})

    try:
        while True:
            message = await websocket.receive_json()
            if message.get("interaction_type") != "response_required":
                if message.get("response_type") == "ping_pong": await websocket.send_json({"response_type": "ping_pong"})
                continue
            response_id = int(message.get("response_id", 0))
            if response_id <= latest_response_id or response_id in store.processed_voice_responses[call_id]: continue
            latest_response_id = response_id
            store.processed_voice_responses[call_id].add(response_id)
            transcript = message.get("transcript", [])
            learner_turns = [item.get("content", "") for item in transcript if item.get("role") == "user"]
            if not learner_turns: continue
            if pending_task and not pending_task.done():
                pending_task.cancel()
            pending_task = asyncio.create_task(respond(response_id, learner_turns[-1]))
    except WebSocketDisconnect:
        if pending_task and not pending_task.done(): pending_task.cancel()
        await store.publish(session.id, {"type": "call_status", "status": "disconnected", "call_id": call_id})


@app.post("/vaani/webhook")
async def vaani_webhook(payload: dict):
    call_id = payload.get("call_id") or payload.get("room_name")
    if not call_id or call_id not in store.call_to_consultation:
        return {"status": "ignored"}
    session = store.by_call(call_id)
    event = payload.get("event")
    event_key = (call_id, str(event))
    if event_key in store.processed_webhook_events:
        return {"status": "duplicate_ignored"}
    store.processed_webhook_events.add(event_key)
    await store.publish(session.id, {"type": "call_status", "status": event, "call_id": call_id})
    if event == "call_postprocessing":
        session.status = "completed"
        report = await add_evaluator_feedback(session, evaluate(session))
        await store.publish(session.id, {"type": "evaluation_ready", "report": report.model_dump()})
    return {"status": "ok"}


@app.post("/consultations/{consultation_id}/turns")
async def submit_turn(consultation_id: str, body: TurnRequest):
    session = store.get(consultation_id)
    # Browser live voice uses the same validated action path as the Vaani
    # adapter, so spoken orders appear in the live reports panel.
    reply = await process_voice_turn(session, body.text) if body.input_mode == "browser_live" else await add_turn(session, body.text)
    return {"reply": reply, "consultation": public_session(session)}


@app.post("/consultations/{consultation_id}/investigations")
def submit_investigation(consultation_id: str, body: InvestigationRequest):
    result = order_investigation(store.get(consultation_id), body.investigation_id)
    return result


@app.post("/consultations/{consultation_id}/differentials")
def submit_differentials(consultation_id: str, body: DifferentialsRequest):
    session = store.get(consultation_id)
    if session.status != "active": raise HTTPException(status_code=422, detail="Consultation is already completed")
    session.differentials = body.differentials
    return public_session(session)


@app.post("/consultations/{consultation_id}/complete")
async def complete_consultation(consultation_id: str, body: CompleteRequest):
    session = store.get(consultation_id)
    if session.status != "active": raise HTTPException(status_code=422, detail="Consultation is already completed")
    session.final_diagnosis, session.management_plan, session.status = body.final_diagnosis, body.management_plan, "completed"
    return await add_evaluator_feedback(session, evaluate(session))


@app.get("/consultations/{consultation_id}/evaluation")
async def get_evaluation(consultation_id: str):
    session = store.get(consultation_id)
    if session.status != "completed": raise HTTPException(status_code=422, detail="Complete the consultation first")
    return await add_evaluator_feedback(session, evaluate(session))


# Docker copies the static Next.js export here. All API/WebSocket routes above
# take priority, so one HTTPS/WSS origin can serve the full MVP.
frontend_out = Path(__file__).resolve().parents[2] / "frontend" / "out"
if frontend_out.is_dir():
    app.mount("/", StaticFiles(directory=frontend_out, html=True), name="frontend")
