import re
import json
from collections import defaultdict

import httpx
from fastapi import HTTPException

from .case_store import get_case
from .config import settings
from .models import ClinicalCase, ConsultationState, EvaluationReport, TranscriptTurn


class ConsultationStore:
    def __init__(self) -> None:
        self.sessions: dict[str, ConsultationState] = {}
        self.call_to_consultation: dict[str, str] = {}
        self.events: dict[str, list[dict]] = defaultdict(list)
        self.subscribers: dict[str, set] = defaultdict(set)
        self.processed_webhook_events: set[tuple[str, str]] = set()
        self.processed_voice_responses: dict[str, set[int]] = defaultdict(set)

    def create(self, case_id: str) -> ConsultationState:
        get_case(case_id)
        session = ConsultationState(case_id=case_id)
        self.sessions[session.id] = session
        return session

    def get(self, consultation_id: str) -> ConsultationState:
        session = self.sessions.get(consultation_id)
        if not session:
            raise HTTPException(status_code=404, detail="Consultation not found")
        return session

    def map_call(self, consultation_id: str, call_id: str) -> None:
        self.call_to_consultation[call_id] = consultation_id

    def by_call(self, call_id: str) -> ConsultationState:
        consultation_id = self.call_to_consultation.get(call_id)
        if not consultation_id:
            raise HTTPException(status_code=404, detail="Vaani call is not mapped to a consultation")
        return self.get(consultation_id)

    async def publish(self, consultation_id: str, event: dict) -> None:
        self.events[consultation_id].append(event)
        for websocket in list(self.subscribers[consultation_id]):
            try:
                await websocket.send_json(event)
            except Exception:
                self.subscribers[consultation_id].discard(websocket)


store = ConsultationStore()


async def extract_action(learner_text: str, case: ClinicalCase) -> dict:
    """Return a conservative action; only known investigation IDs may mutate state."""
    lower = learner_text.lower()
    matches = [item.id for item in case.investigations if item.name.lower() in lower or item.id.lower() in lower]
    if "order" in lower or "test" in lower or "investigation" in lower:
        return {"action": "order_investigations", "investigation_ids": matches}
    return {"action": "none", "investigation_ids": []}


async def process_voice_turn(session: ConsultationState, learner_text: str) -> str:
    case = get_case(session.case_id)
    action = await extract_action(learner_text, case)
    for investigation_id in action["investigation_ids"]:
        investigation = order_investigation(session, investigation_id)
        await store.publish(session.id, {"type": "investigation_ordered", "investigation_id": investigation.id, "name": investigation.name})
        await store.publish(session.id, {"type": "investigation_result", "investigation_id": investigation.id, "name": investigation.name, "summary": investigation.summary, "interpretation": investigation.interpretation})
    reply = await add_turn(session, learner_text)
    await store.publish(session.id, {"type": "transcript_turn", "role": "learner", "text": learner_text})
    await store.publish(session.id, {"type": "transcript_turn", "role": "patient", "text": reply})
    return reply


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", value.lower())


def lexical_facts(case: ClinicalCase, learner_text: str, revealed: set[str]) -> list:
    question = _normalise(learner_text)
    matches = [
        fact for fact in case.facts
        if fact.id not in revealed and any(matcher in question for matcher in fact.matchers)
    ]
    return matches[:2]


async def select_facts_with_openrouter(case: ClinicalCase, learner_text: str, session: ConsultationState) -> list:
    """Choose fact IDs only; clinical truth stays in the case file, not the model."""
    if not settings.openrouter_api_key:
        return []
    candidate_facts = [
        {"id": fact.id, "category": fact.category, "text": fact.text}
        for fact in case.facts if fact.id not in session.revealed_fact_ids
    ]
    if not candidate_facts:
        return []
    recent_transcript = [turn.model_dump(mode="json") for turn in session.transcript[-8:]]
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": (
                "You are a clinical-simulation fact selector. Select at most two fact IDs that directly answer "
                "the learner's current question, considering the recent transcript. Never infer, diagnose, or reveal "
                "facts that are not directly requested. Return JSON only: {\"fact_ids\":[\"id\"]}. "
                "Return an empty array when no candidate fact answers the question."
            )},
            {"role": "user", "content": json.dumps({"question": learner_text, "recent_transcript": recent_transcript, "candidate_facts": candidate_facts})},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0,
        "max_tokens": 80,
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openrouter_api_key}", "Content-Type": "application/json", "X-Title": "AI Virtual Patient Simulator"},
                json=payload,
            )
            response.raise_for_status()
            selected_ids = json.loads(response.json()["choices"][0]["message"]["content"]).get("fact_ids", [])
    except (httpx.HTTPError, KeyError, IndexError, TypeError, json.JSONDecodeError):
        return []
    allowed_ids = {fact["id"] for fact in candidate_facts}
    return [fact for fact in case.facts if fact.id in selected_ids and fact.id in allowed_ids][:2]


def safe_conversational_reply(case: ClinicalCase, learner_text: str, is_first_turn: bool) -> str | None:
    question = _normalise(learner_text)
    if "name" in question:
        return f"My name is {case.patient_profile.name}."
    if "old" in question or "age" in question:
        return f"I am {case.patient_profile.age} years old."
    opening_phrases = ("what brings", "what happened", "what problem", "what is wrong", "how can i help", "complaint", "tell me about", "hello")
    words = set(question.split())
    if is_first_turn or any(phrase in question for phrase in opening_phrases) or "hi" in words:
        return f"I came because of {case.presenting_complaint.lower()}"
    return None


async def patient_reply(case: ClinicalCase, learner_text: str, facts: list, is_first_turn: bool) -> str:
    if not facts:
        safe_reply = safe_conversational_reply(case, learner_text, is_first_turn)
        if safe_reply:
            return safe_reply
        return "I am not sure what you mean. Could you ask me that in another way?"
    fallback = " ".join(fact.text for fact in facts)
    if not settings.openrouter_api_key:
        return fallback

    system = (
        "You are a fictional patient in a medical education simulation. "
        "Reply in first person with one short, natural spoken response. "
        "Use only the supplied allowed facts. Never name a diagnosis, recommend treatment, "
        "or add facts. Answer the learner's question directly and naturally in one or two sentences."
    )
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": (
                f"Patient: {case.patient_profile.name}, {case.patient_profile.age}; "
                f"style: {case.patient_profile.communication_style}.\n"
                f"Learner question: {learner_text}\n"
                f"Allowed facts: {[fact.text for fact in facts]}"
            )},
        ],
        "temperature": 0.2,
        "max_tokens": 100,
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.openrouter_api_key}", "Content-Type": "application/json", "X-Title": "AI Virtual Patient Simulator"},
                json=payload,
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"].strip()
            return text or fallback
    except (httpx.HTTPError, KeyError, IndexError, TypeError):
        return fallback


async def add_turn(session: ConsultationState, learner_text: str) -> str:
    if session.status != "active":
        raise HTTPException(status_code=422, detail="Consultation is already completed")
    case = get_case(session.case_id)
    facts = lexical_facts(case, learner_text, session.revealed_fact_ids)
    if not facts:
        facts = await select_facts_with_openrouter(case, learner_text, session)
    reply = await patient_reply(case, learner_text, facts, is_first_turn=not session.transcript)
    session.revealed_fact_ids.update(fact.id for fact in facts)
    session.transcript.extend([TranscriptTurn(role="learner", text=learner_text), TranscriptTurn(role="patient", text=reply)])
    return reply


def order_investigation(session: ConsultationState, investigation_id: str):
    if session.status != "active":
        raise HTTPException(status_code=422, detail="Consultation is already completed")
    investigation = next((item for item in get_case(session.case_id).investigations if item.id == investigation_id), None)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation is not available for this case")
    if investigation_id not in session.ordered_investigation_ids:
        session.ordered_investigation_ids.append(investigation_id)
    return investigation


def evaluate(session: ConsultationState) -> EvaluationReport:
    case = get_case(session.case_id)
    red_flags = [fact for fact in case.facts if fact.is_red_flag]
    revealed = {fact.id for fact in case.facts if fact.id in session.revealed_fact_ids}
    history = round(100 * len(revealed) / max(len(red_flags), 1))
    history = min(history, 100)
    ordered = {item.id for item in case.investigations if item.id in session.ordered_investigation_ids}
    recommended = {item.id for item in case.investigations if item.recommended}
    investigations = round(100 * len(ordered & recommended) / max(len(recommended), 1))
    diagnosis = _normalise(session.final_diagnosis or "")
    reasoning = 100 if _normalise(case.expected_diagnosis) in diagnosis else 0
    management_text = _normalise(" ".join(session.management_plan))
    management_hits = sum(1 for item in case.expected_management if _normalise(item) in management_text)
    management = round(100 * management_hits / max(len(case.expected_management), 1))
    communication = 80 if len(session.transcript) >= 4 else 50
    scores = {"history_taking": history, "clinical_reasoning": reasoning, "investigation_selection": investigations, "communication": communication, "management": management}
    missed = [fact.text for fact in red_flags if fact.id not in revealed]
    unnecessary = [item.name for item in case.investigations if item.id in ordered and not item.recommended]
    strengths = []
    if history >= 75: strengths.append("Elicited key red-flag history.")
    if reasoning == 100: strengths.append("Reached the expected diagnosis.")
    if investigations >= 75: strengths.append("Selected appropriate initial investigations.")
    evidence = [turn.text for turn in session.transcript if turn.role == "learner"]
    overall = round(sum(scores.values()) / len(scores))
    feedback = "Review the missed items and use the transcript evidence to guide the next consultation."
    return EvaluationReport(overall_score=overall, scores=scores, missed_items=missed, unnecessary_actions=unnecessary, strengths=strengths, evidence=evidence, feedback=feedback)


async def add_evaluator_feedback(session: ConsultationState, report: EvaluationReport) -> EvaluationReport:
    """Evaluator Agent: qualitative coaching may enrich, never overwrite deterministic scores."""
    if not settings.openrouter_api_key:
        return report
    case = get_case(session.case_id)
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": (
                "You are an evaluator for a fictional medical-training simulation. Give concise, supportive feedback "
                "using only the supplied deterministic report and learner transcript. Do not give real-patient medical "
                "advice, change scores, or claim evidence not in the transcript. Return JSON only: {\"feedback\":string}."
            )},
            {"role": "user", "content": json.dumps({"case_title": case.title, "report": report.model_dump(), "transcript": [turn.model_dump(mode="json") for turn in session.transcript]})},
        ],
        "response_format": {"type": "json_object"}, "temperature": 0.2, "max_tokens": 180,
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {settings.openrouter_api_key}", "Content-Type": "application/json", "X-Title": "AI Virtual Patient Simulator"}, json=payload)
            response.raise_for_status()
            feedback = json.loads(response.json()["choices"][0]["message"]["content"]).get("feedback")
            if isinstance(feedback, str) and feedback.strip():
                report.feedback = feedback.strip()
    except (httpx.HTTPError, KeyError, IndexError, TypeError, json.JSONDecodeError):
        pass
    return report
