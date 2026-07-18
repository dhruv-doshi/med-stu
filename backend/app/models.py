from datetime import datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class PatientProfile(BaseModel):
    name: str
    age: int
    personality: str
    communication_style: str


class CaseFact(BaseModel):
    id: str
    text: str
    matchers: list[str] = Field(default_factory=list)
    category: str = "history"
    is_red_flag: bool = False


class Investigation(BaseModel):
    id: str
    name: str
    summary: str
    interpretation: str
    recommended: bool = False


class ClinicalCase(BaseModel):
    id: str
    title: str
    specialty: str
    difficulty: str
    learning_objectives: list[str]
    patient_profile: PatientProfile
    presenting_complaint: str
    facts: list[CaseFact]
    investigations: list[Investigation]
    expected_differentials: list[str]
    expected_management: list[str]
    expected_diagnosis: str


class TranscriptTurn(BaseModel):
    role: Literal["learner", "patient"]
    text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ConsultationState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    status: Literal["active", "completed"] = "active"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    transcript: list[TranscriptTurn] = Field(default_factory=list)
    revealed_fact_ids: set[str] = Field(default_factory=set)
    ordered_investigation_ids: list[str] = Field(default_factory=list)
    differentials: list[str] = Field(default_factory=list)
    final_diagnosis: str | None = None
    management_plan: list[str] = Field(default_factory=list)


class CreateConsultationRequest(BaseModel):
    case_id: str


class TurnRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    input_mode: Literal["text", "voice", "browser_live"] = "text"


class InvestigationRequest(BaseModel):
    investigation_id: str


class DifferentialsRequest(BaseModel):
    differentials: list[str] = Field(default_factory=list)


class CompleteRequest(BaseModel):
    final_diagnosis: str | None = None
    management_plan: list[str] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    overall_score: int
    scores: dict[str, int]
    missed_items: list[str]
    unnecessary_actions: list[str]
    strengths: list[str]
    evidence: list[str]
    feedback: str
    rubric_version: str = "1.0"
