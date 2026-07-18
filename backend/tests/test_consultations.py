from fastapi.testclient import TestClient

from app.main import app
from app.services import store

client = TestClient(app)


def setup_function():
    store.sessions.clear(); store.call_to_consultation.clear(); store.events.clear(); store.processed_webhook_events.clear(); store.processed_voice_responses.clear()


def test_case_list_hides_diagnosis():
    response = client.get("/cases")
    assert response.status_code == 200
    assert "expected_diagnosis" not in response.text
    assert len(response.json()) == 5


def test_all_cases_create_and_answer():
    for case in client.get("/cases").json():
        created = client.post("/consultations", json={"case_id": case["id"]})
        assert created.status_code == 200
        reply = client.post(f"/consultations/{created.json()['id']}/turns", json={"text": "Hello, what brings you in today?"})
        assert reply.status_code == 200 and reply.json()["reply"]


def test_chest_pain_golden_path():
    consultation = client.post("/consultations", json={"case_id": "chest_pain_001"}).json()
    cid = consultation["id"]
    turn = client.post(f"/consultations/{cid}/turns", json={"text": "When did it start and does it go to your arm?"})
    assert turn.status_code == 200
    assert "two hours" in turn.json()["reply"]
    ecg = client.post(f"/consultations/{cid}/investigations", json={"investigation_id": "ecg"})
    assert ecg.json()["interpretation"] == "Inferior wall myocardial infarction."
    report = client.post(f"/consultations/{cid}/complete", json={"final_diagnosis": "Acute coronary syndrome", "management_plan": ["urgent cardiology referral", "antiplatelet therapy"]})
    assert report.status_code == 200
    assert report.json()["scores"]["clinical_reasoning"] == 100


def test_common_opening_question_gets_presenting_complaint():
    cid = client.post("/consultations", json={"case_id": "chest_pain_001"}).json()["id"]
    reply = client.post(f"/consultations/{cid}/turns", json={"text": "Hello, what brings you in today?"}).json()["reply"]
    assert "chest discomfort" in reply


def test_common_history_wording_reveals_safe_fact():
    cid = client.post("/consultations", json={"case_id": "chest_pain_001"}).json()["id"]
    reply = client.post(f"/consultations/{cid}/turns", json={"text": "How long have you had this and does it travel anywhere?"}).json()["reply"]
    assert "two hours" in reply and "left arm" in reply


def test_pain_scale_question_gets_authored_severity():
    cid = client.post("/consultations", json={"case_id": "chest_pain_001"}).json()["id"]
    reply = client.post(f"/consultations/{cid}/turns", json={"text": "How much is it hurting on a scale of 1 to 10?"}).json()["reply"]
    assert "8 out of 10" in reply


def test_follow_up_history_questions_use_new_authored_facts():
    cid = client.post("/consultations", json={"case_id": "chest_pain_001"}).json()["id"]
    constant = client.post(f"/consultations/{cid}/turns", json={"text": "Has the pain been constant?"}).json()["reply"]
    previous = client.post(f"/consultations/{cid}/turns", json={"text": "Has this happened to you ever before?"}).json()["reply"]
    assert "constant" in constant
    assert "not had pain like this before" in previous


def test_unknown_investigation_is_rejected():
    cid = client.post("/consultations", json={"case_id": "chest_pain_001"}).json()["id"]
    assert client.post(f"/consultations/{cid}/investigations", json={"investigation_id": "mri"}).status_code == 404


def test_byol_handshake_and_voice_turn_stream():
    consultation = client.post("/consultations", json={"case_id": "chest_pain_001"}).json()
    store.map_call(consultation["id"], "call-test")
    with client.websocket_connect("/vaani/byol/call-test") as websocket:
        assert websocket.receive_json()["interaction_type"] == "config"
        assert websocket.receive_json()["interaction_type"] == "greeting"
        websocket.send_json({"interaction_type": "response_required", "response_id": 1, "transcript": [{"role": "user", "content": "What brings you in today?"}]})
        response = websocket.receive_json()
        assert response["response_type"] == "response"
        assert "chest discomfort" in response["content"]


def test_voice_order_action_publishes_report():
    consultation = client.post("/consultations", json={"case_id": "chest_pain_001"}).json()
    session = store.get(consultation["id"])
    import asyncio
    asyncio.run(__import__("app.services", fromlist=["process_voice_turn"]).process_voice_turn(session, "Please order an ECG"))
    assert "ecg" in session.ordered_investigation_ids
    assert any(event["type"] == "investigation_result" for event in store.events[session.id])


def test_webhook_postprocessing_is_idempotent():
    consultation = client.post("/consultations", json={"case_id": "chest_pain_001"}).json()
    store.map_call(consultation["id"], "call-hook")
    payload = {"call_id": "call-hook", "event": "call_postprocessing"}
    assert client.post("/vaani/webhook", json=payload).json()["status"] == "ok"
    assert client.post("/vaani/webhook", json=payload).json()["status"] == "duplicate_ignored"
