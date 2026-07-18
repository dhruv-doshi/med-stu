from fastapi.testclient import TestClient

from app.main import app
from app.services import store

client = TestClient(app)


def setup_function(): store.sessions.clear()


def test_case_list_hides_diagnosis():
    response = client.get("/cases")
    assert response.status_code == 200
    assert "expected_diagnosis" not in response.text


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


def test_unknown_investigation_is_rejected():
    cid = client.post("/consultations", json={"case_id": "chest_pain_001"}).json()["id"]
    assert client.post(f"/consultations/{cid}/investigations", json={"investigation_id": "mri"}).status_code == 404
