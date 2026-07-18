# AI Virtual Patient Simulator

## Project Summary

Build a real-time AI clinical simulation platform where a doctor or medical student conducts a teleconsultation with an AI patient.

The AI patient should:

- Speak naturally through voice
- Reveal information only when appropriately asked
- Maintain a consistent medical history and personality
- Respond according to a hidden clinical case
- Allow the user to order investigations
- Evaluate the consultation after completion

The product should feel like a realistic video or voice consultation rather than a chatbot.

## Primary Goal

Create a portfolio-grade applied AI project demonstrating:

- Real-time voice AI
- LLM orchestration
- Stateful conversations
- Structured generation
- Clinical simulation
- Evaluation systems
- Tool calling
- Observability
- Production-oriented architecture

This is an educational simulation product, not a diagnostic tool for real patients.

## Target Users

- MBBS students
- Medical interns
- Residents
- Doctors preparing for OSCE-style examinations
- Telemedicine teams training communication and diagnosis workflows

## Core User Flow

1. User selects a clinical case.
2. A simulated teleconsultation begins.
3. The user speaks to the AI patient.
4. The patient answers naturally and consistently.
5. The user may ask history-taking questions, request examinations, order investigations, state differential diagnoses, and submit a final diagnosis and management plan.
6. The consultation ends.
7. The system generates a detailed evaluation report.

## MVP Scope

Build the first version around 3–5 common outpatient cases:

- Acute chest pain
- Type 2 diabetes follow-up
- Migraine
- Upper respiratory infection
- Abdominal pain

Each case should contain:

- Hidden diagnosis
- Demographics
- Presenting complaint
- Symptom timeline
- Medical history
- Medication history
- Family history
- Social history
- Red flags
- Information revealed only when specifically asked
- Expected differential diagnoses
- Recommended investigations
- Unnecessary investigations
- Expected management approach

## High-Level Architecture

```text
Doctor / Student
       |
       v
Web or Mobile Client
       |
       v
Real-Time Voice Layer
STT + TTS + interruption handling
       |
       v
Conversation Orchestrator
       |
       +----------------------+
       |                      |
       v                      v
Patient Agent           Clinical State Engine
       |                      |
       +----------+-----------+
                  |
                  v
         Investigation Service
                  |
                  v
            Evaluation Engine
                  |
                  v
          Performance Dashboard
```

## Recommended Components

### 1. Patient Agent

The patient-facing agent should:

- Speak in first person
- Never reveal the hidden diagnosis
- Never provide information that has not been asked for unless clinically natural
- Maintain emotional tone and personality
- Avoid contradicting previous answers
- Remember what the doctor has already asked
- Respond according to the case state

Example patient personality:

```json
{
  "name": "Ramesh",
  "age": 58,
  "personality": "anxious but cooperative",
  "communication_style": "brief answers unless prompted",
  "health_literacy": "moderate"
}
```

### 2. Clinical State Engine

This should be deterministic wherever possible.

Responsibilities:

- Store the ground-truth case
- Track questions already asked
- Track information already revealed
- Track investigation requests
- Track differential diagnoses
- Track final diagnosis
- Prevent patient-agent hallucination
- Enforce scenario rules

Example state:

```json
{
  "case_id": "chest_pain_001",
  "diagnosis": "acute coronary syndrome",
  "revealed_facts": [
    "central chest pain",
    "pain started 2 hours ago"
  ],
  "hidden_facts": [
    "smoking history",
    "radiation to left arm"
  ],
  "ordered_tests": [],
  "doctor_differentials": [],
  "consultation_status": "active"
}
```

### 3. Investigation Service

The doctor should be able to request tests such as:

- CBC
- Blood glucose
- Troponin
- ECG
- Chest X-ray
- Liver function tests
- Kidney function tests
- CT
- MRI

The service should return predefined structured results linked to the case.

```json
{
  "test": "ECG",
  "status": "completed",
  "result": {
    "summary": "ST-segment elevation in leads II, III and aVF",
    "interpretation": "Inferior wall myocardial infarction"
  }
}
```

Do not generate critical investigation values freely during runtime. Store expected results in the case definition.

### 4. Evaluation Engine

The evaluator should assess:

- History completeness
- Red-flag identification
- Differential diagnosis quality
- Final diagnosis accuracy
- Investigation appropriateness
- Management plan
- Communication
- Empathy
- Consultation structure
- Time efficiency
- Cost awareness

```json
{
  "overall_score": 78,
  "scores": {
    "history_taking": 82,
    "clinical_reasoning": 75,
    "investigation_selection": 70,
    "communication": 88,
    "management": 72
  },
  "missed_items": [
    "Did not ask about smoking history",
    "Did not ask about diaphoresis"
  ],
  "unnecessary_actions": [
    "Ordered MRI before ECG"
  ],
  "strengths": [
    "Maintained a calm tone",
    "Considered acute coronary syndrome early"
  ]
}
```

Use a hybrid evaluator:

- Deterministic rubric scoring
- LLM-based qualitative feedback
- Structured JSON output
- Explicit evidence from transcript

## Agent Design

Avoid implementing everything as one large prompt.

Suggested agents or services:

- Patient Agent: generates patient responses
- Examiner Agent: evaluates whether important questions were asked
- Clinical Reasoning Evaluator: assesses differentials, diagnosis, and management
- Communication Evaluator: assesses empathy, clarity, and professionalism
- Case Generator: creates structured educational cases for faculty review

The runtime system should work even if only the Patient Agent and Evaluator are implemented initially.

## Suggested Technology Stack

### Frontend

- React or Next.js
- TypeScript
- WebRTC or real-time audio SDK
- Tailwind CSS
- Audio waveform and live transcript
- Consultation timer
- Investigation-ordering panel
- Evaluation dashboard

### Backend

- FastAPI
- Python
- PostgreSQL
- Redis
- WebSockets
- Celery or background workers where needed
- Pydantic models
- Docker Compose

### AI Layer

- LLM with structured-output support
- Streaming speech-to-text
- Streaming text-to-speech
- Voice activity detection
- Barge-in support
- Prompt versioning
- Tracing and evaluation logs

Vaani AI can be used as the speech layer if it provides suitable APIs for streaming speech-to-text, streaming text-to-speech, low-latency audio, interruption handling, and Indian-accent or multilingual speech.

Keep the speech provider behind an interface so it can be replaced later.

## Suggested Repository Structure

```text
virtual-patient-simulator/
├── apps/
│   ├── web/
│   └── api/
├── services/
│   ├── voice/
│   ├── patient_agent/
│   ├── evaluator/
│   ├── investigations/
│   └── case_engine/
├── packages/
│   ├── shared_types/
│   ├── prompts/
│   └── evaluation_rubrics/
├── cases/
│   ├── chest_pain_001.json
│   ├── diabetes_followup_001.json
│   └── abdominal_pain_001.json
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Core Data Models

### Clinical Case

```python
from typing import List, Dict, Optional
from pydantic import BaseModel


class InvestigationResult(BaseModel):
    test_name: str
    result: Dict
    interpretation: Optional[str] = None


class ClinicalCase(BaseModel):
    case_id: str
    title: str
    diagnosis: str
    demographics: Dict
    presenting_complaint: str
    history: Dict
    red_flags: List[str]
    reveal_rules: Dict[str, List[str]]
    expected_differentials: List[str]
    recommended_investigations: List[str]
    unnecessary_investigations: List[str]
    investigation_results: List[InvestigationResult]
    expected_management: List[str]
```

### Consultation State

```python
from datetime import datetime
from typing import List, Dict
from pydantic import BaseModel, Field


class ConsultationState(BaseModel):
    consultation_id: str
    case_id: str
    started_at: datetime
    status: str = "active"
    revealed_facts: List[str] = Field(default_factory=list)
    asked_questions: List[str] = Field(default_factory=list)
    ordered_investigations: List[str] = Field(default_factory=list)
    differentials: List[str] = Field(default_factory=list)
    final_diagnosis: str | None = None
    management_plan: List[str] = Field(default_factory=list)
    transcript: List[Dict] = Field(default_factory=list)
```

## Example Patient System Prompt

```text
You are simulating a patient in a medical education scenario.

Rules:

1. Speak only as the patient.
2. Never reveal the diagnosis.
3. Use only facts present in the supplied case data.
4. Do not volunteer hidden details unless the doctor's question naturally asks for them.
5. Keep all answers consistent with previous answers.
6. If the doctor asks an unclear question, ask for clarification.
7. Do not provide medical advice.
8. Do not act as an examiner.
9. Keep responses conversational and realistic.
10. Use short spoken answers unless the doctor requests more detail.

Current patient profile:
{{patient_profile}}

Known case facts:
{{case_facts}}

Already revealed:
{{revealed_facts}}

Conversation history:
{{conversation_history}}
```

## Example Evaluation Prompt

```text
Evaluate the consultation using only:

- The case rubric
- The consultation transcript
- The investigations ordered
- The submitted differential diagnoses
- The final diagnosis
- The management plan

Return valid JSON.

Do not reward information that was never stated by the learner.
Every criticism must reference transcript evidence or a missing rubric item.
Do not provide real-world medical advice to an actual patient.

Required output:

{
  "overall_score": 0,
  "scores": {
    "history_taking": 0,
    "clinical_reasoning": 0,
    "investigation_selection": 0,
    "communication": 0,
    "management": 0
  },
  "missed_items": [],
  "unnecessary_actions": [],
  "strengths": [],
  "feedback": ""
}
```

## Initial API Endpoints

```text
POST   /cases
GET    /cases
GET    /cases/{case_id}

POST   /consultations
GET    /consultations/{consultation_id}
POST   /consultations/{consultation_id}/message
POST   /consultations/{consultation_id}/investigations
POST   /consultations/{consultation_id}/differentials
POST   /consultations/{consultation_id}/complete

GET    /consultations/{consultation_id}/evaluation

WS     /consultations/{consultation_id}/stream
```

## MVP Screens

### Case Selection

- Case title
- Specialty
- Difficulty
- Approximate duration
- Learning objectives

### Consultation Screen

- AI patient avatar
- Voice call controls
- Live transcript
- Timer
- Order-investigation button
- Add-differential button
- End-consultation button

### Evaluation Screen

- Overall score
- Section-wise scores
- Timeline of consultation
- Missed questions
- Correct and incorrect decisions
- Better differential pathway
- Communication feedback
- Transcript replay

## Development Phases

### Phase 1: Text-Based Prototype

Build:

- Case JSON format
- Patient agent
- Consultation state
- Text chat UI
- Investigation ordering
- Final diagnosis submission
- Basic evaluator

Do not begin with voice.

### Phase 2: Voice Integration

Add:

- Streaming STT
- Streaming TTS
- WebSocket session
- Voice activity detection
- Barge-in
- Partial transcript display

### Phase 3: Evaluation Quality

Add:

- Deterministic scoring rubric
- Transcript evidence
- Prompt versioning
- Evaluation regression tests
- Faculty-review workflow

### Phase 4: Portfolio Polish

Add:

- Analytics dashboard
- Case-authoring interface
- Consultation replay
- Latency tracking
- Docker deployment
- Architecture documentation
- Demo video
- Evaluation benchmark report

## Testing Requirements

### Patient Consistency Tests

Verify that the patient:

- Does not reveal diagnosis
- Does not invent symptoms
- Does not contradict age or history
- Reveals hidden facts only when asked
- Remembers previously answered questions

### Evaluation Tests

Create fixed consultations with expected scores:

- Excellent consultation
- Correct diagnosis with poor communication
- Incorrect diagnosis with good history
- Excessive investigations
- Missed red flags

### Voice Tests

Measure:

- Speech-to-text latency
- LLM latency
- Text-to-speech latency
- Time to first audio
- Interruption success rate
- Conversation recovery after network loss

## Important Safety Constraints

- Clearly label the platform as an educational simulator.
- Do not allow use for real patient diagnosis.
- Do not expose hidden case answers during an active consultation.
- Do not use real patient data in the MVP.
- Do not train on private medical conversations without explicit consent.
- Maintain audit logs for generated cases and evaluations.
- Require expert review before presenting generated clinical content as educationally valid.

## Portfolio Differentiators

The project will be significantly stronger if it demonstrates:

- Real-time voice interaction
- Deterministic state plus LLM generation
- Case-grounded responses
- Tool calling for investigations
- Automatic evaluation with transcript evidence
- Latency and reliability metrics
- Prompt and model versioning
- Regression testing for AI behavior
- Multilingual or Indian-accent support
- Faculty-editable case definitions

## First Implementation Task

Start with a text-only chest-pain case.

Deliver:

1. One structured clinical case JSON
2. FastAPI consultation endpoints
3. Stateful patient conversation
4. Investigation ordering
5. Final diagnosis submission
6. Structured evaluation JSON
7. Simple React interface
8. Docker Compose setup
9. Unit tests for case consistency
10. README instructions for local setup

Do not add voice until the complete text-based flow works reliably.

## Definition of Done for MVP

The MVP is complete when:

- A user can select a case
- The user can conduct a consultation
- The patient remains consistent
- The user can order investigations
- The user can submit differentials
- The user can submit a final diagnosis
- The system produces a structured evaluation
- The evaluation cites transcript evidence
- The complete system runs locally through Docker Compose
- Automated tests cover the main clinical state transitions
