import json
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException

from .models import ClinicalCase

CASES_DIR = Path(__file__).parent.parent / "data" / "cases"


@lru_cache
def load_cases() -> dict[str, ClinicalCase]:
    cases: dict[str, ClinicalCase] = {}
    for path in CASES_DIR.glob("*.json"):
        case = ClinicalCase.model_validate(json.loads(path.read_text()))
        cases[case.id] = case
    return cases


def get_case(case_id: str) -> ClinicalCase:
    case = load_cases().get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


def public_case(case: ClinicalCase) -> dict:
    return {
        "id": case.id,
        "title": case.title,
        "specialty": case.specialty,
        "difficulty": case.difficulty,
        "learning_objectives": case.learning_objectives,
        "presenting_complaint": case.presenting_complaint,
    }
