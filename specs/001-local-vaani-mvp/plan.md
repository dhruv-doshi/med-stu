# Implementation Plan: Local Vaani Voice MVP

**Feature**: `001-local-vaani-mvp` | **Date**: 2026-07-18 | **Spec**: [spec.md](spec.md)

## Summary

Build a local web application where the frontend owns the learner experience and FastAPI owns all protected clinical state. JSON case files provide deterministic clinical truth; a structured-output LLM produces only patient wording and qualitative feedback. Vaani is used exclusively for microphone/speech transport, not for case-state decisions or scoring.

## Technical Context

- **Frontend**: Next.js + TypeScript; browser microphone controls, transcript, case picker, investigation panel, and evaluation page.
- **Backend**: Python 3.11+ + FastAPI + Pydantic.
- **Storage for MVP**: Authored JSON case files and process-memory sessions. Restarting the backend resets sessions.
- **AI**: Provider-neutral structured-output LLM adapter; server sends only case-allowed facts and current revealed state.
- **Voice**: `VoiceProvider` with `VaaniVoiceProvider` and `MockVoiceProvider`; default target is the Vaani Labs browser-oriented WebSocket/session API.
- **Tests**: pytest for backend/state/rubric tests; frontend smoke/e2e test for the chest-pain path.
- **Constraints**: Smooth local demo in approximately two hours; no database, Docker, telephony, authentication, or production infrastructure in this feature.

## Constitution Check

| Gate | Status | Decision |
|---|---|---|
| Educational-only language and fictional data | Pass | Persistent disclaimer; authored fictional cases only. |
| Deterministic clinical truth | Pass | JSON case/rubric/investigation data remain authoritative. |
| Demo-safe fallback | Pass | Text and mock voice mode work without Vaani credentials. |
| Evidence-backed evaluation | Pass | Deterministic scoring and transcript references are required. |

## Architecture and data flow

```text
Browser (Next.js)
  ├─ text controls / transcript / investigations / evaluation
  └─ microphone + audio controls
          │
          ├─ VaaniVoiceProvider (speech in/out only; optional)
          └─ FastAPI consultation API
                  ├─ CaseRepository (authored JSON)
                  ├─ ConsultationStateService (in-memory)
                  ├─ PatientResponseService (LLM constrained by state)
                  └─ EvaluationService (deterministic rubric + LLM feedback)
```

The browser never receives hidden diagnosis data, full rubric data, or unrevealed facts. It sends the learner transcript text to FastAPI. For voice mode, Vaani transcribes learner speech and plays patient speech; FastAPI remains the sole source of the patient reply text.

## Public API

See [contracts/http-api.md](contracts/http-api.md). The MVP exposes consultation creation, turn submission, investigation ordering, differentials, completion, and evaluation retrieval. All responses use JSON and include a consultation identifier.

## Delivery sequence

1. Scaffold frontend/backend, shared JSON models, the chest-pain case, and in-memory state.
2. Implement and test text consultation turns, reveal logic, investigations, final submission, and deterministic evaluation.
3. Add four schema-compatible cases and smoke fixtures.
4. Add the Vaani adapter, mock fallback, microphone/audio controls, and transcript synchronization.
5. Execute the demo script and fix only issues blocking the local flow.

## Deferred scale architecture

The online version replaces process memory with PostgreSQL and Redis, introduces a job queue for evaluation, serves frontend/API in containers, uses managed secrets and authenticated sessions, and publishes traces/metrics/logs. Detailed scale requirements belong in `003-production-platform` after the local demo is accepted.
