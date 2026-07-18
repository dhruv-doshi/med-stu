# Task List: Local Vaani Voice MVP

## Stage 1 — Runnable text slice

- [X] Create Next.js and FastAPI application skeletons with local environment examples.
- [X] Define Pydantic case/state/evaluation models and JSON case loader.
- [X] Author chest-pain golden case with facts, reveal rules, ECG/troponin, and rubric.
- [X] Implement consultation creation, turn handling, investigation ordering, submission, and completion APIs.
- [X] Implement deterministic reveal and scoring tests before LLM response wiring.
- [X] Build case selection and text consultation UI.

## Stage 2 — Evaluation and case coverage

- [X] Add structured qualitative feedback adapter constrained by deterministic results and transcript evidence.
- [X] Build evaluation view with category scores, missed items, strengths, and evidence.
- [X] Author diabetes, migraine, URI, and abdominal-pain cases using the same schema.
- [X] Add smoke fixtures for every case and golden chest-pain evaluation regression.

## Stage 3 — Vaani BYOL phone-call runtime

- [X] Add Vaani configuration, call dispatch, agent/call mapping, and a browser live-event WebSocket.
- [X] Implement the BYOL handshake, transcript-to-state turn handling, response chunk streaming, and abandoned-turn cancellation.
- [X] Add structured spoken-action extraction for investigation orders and broadcast live browser report events.
- [X] Add Vaani lifecycle/post-processing webhook handling, evaluation trigger, and webhook/idempotency tests.
- [X] Replace browser voice fallback as the primary flow with call launch, call state, live transcript, live reports, and post-call evaluation.
- [X] Test Vaani no-fallback behavior, BYOL reconnect, live ECG order, native interruption, and browser text recovery.

## Stage 4 — Demo hardening

- [X] Add educational disclaimers, reset control, loading states, and concise local setup instructions.
- [X] Package a single-service Docker deployment that serves the static frontend from FastAPI and documents Railway/Render configuration.
- [X] Add and verify a free browser-live STT/TTS demo mode with interrupt cancellation and case-safe spoken investigation orders.
- [ ] Run the scripted chest-pain demo in a clean browser profile.
- [ ] Record known limitations and move production requirements into the next feature specification.
