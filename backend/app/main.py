from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .case_store import get_case, load_cases, public_case
from .models import CompleteRequest, CreateConsultationRequest, DifferentialsRequest, InvestigationRequest, TurnRequest
from .services import add_turn, evaluate, order_investigation, store

app = FastAPI(title="AI Virtual Patient Simulator", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])


def public_session(session):
    return {"id": session.id, "case_id": session.case_id, "status": session.status, "transcript": [turn.model_dump(mode="json") for turn in session.transcript], "ordered_investigation_ids": session.ordered_investigation_ids, "differentials": session.differentials}


@app.get("/health")
def health(): return {"status": "ok"}


@app.get("/cases")
def list_cases(): return [public_case(case) for case in load_cases().values()]


@app.post("/consultations")
def create_consultation(body: CreateConsultationRequest): return public_session(store.create(body.case_id))


@app.get("/consultations/{consultation_id}")
def get_consultation(consultation_id: str): return public_session(store.get(consultation_id))


@app.post("/consultations/{consultation_id}/turns")
async def submit_turn(consultation_id: str, body: TurnRequest):
    session = store.get(consultation_id)
    reply = await add_turn(session, body.text)
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
def complete_consultation(consultation_id: str, body: CompleteRequest):
    session = store.get(consultation_id)
    if session.status != "active": raise HTTPException(status_code=422, detail="Consultation is already completed")
    session.final_diagnosis, session.management_plan, session.status = body.final_diagnosis, body.management_plan, "completed"
    return evaluate(session)


@app.get("/consultations/{consultation_id}/evaluation")
def get_evaluation(consultation_id: str):
    session = store.get(consultation_id)
    if session.status != "completed": raise HTTPException(status_code=422, detail="Complete the consultation first")
    return evaluate(session)
