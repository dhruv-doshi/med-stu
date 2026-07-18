# Task List: Local Vaani Voice MVP

## Stage 1 — Runnable text slice

- [X] Create Next.js and FastAPI application skeletons with local environment examples.
- [X] Define Pydantic case/state/evaluation models and JSON case loader.
- [X] Author chest-pain golden case with facts, reveal rules, ECG/troponin, and rubric.
- [X] Implement consultation creation, turn handling, investigation ordering, submission, and completion APIs.
- [X] Implement deterministic reveal and scoring tests before LLM response wiring.
- [X] Build case selection and text consultation UI.

## Stage 2 — Evaluation and case coverage

- [ ] Add structured qualitative feedback adapter constrained by deterministic results and transcript evidence.
- [ ] Build evaluation view with category scores, missed items, strengths, and evidence.
- [ ] Author diabetes, migraine, URI, and abdominal-pain cases using the same schema.
- [ ] Add smoke fixtures for every case and golden chest-pain evaluation regression.

## Stage 3 — Vaani voice

- [ ] Define `VoiceProvider`, mock implementation, environment validation, and provider-error contract.
- [ ] Implement Vaani Labs browser-session creation on the backend.
- [ ] Add microphone controls, transcript synchronization, and patient audio playback in the frontend.
- [ ] Test text fallback, denied microphone permission, unavailable Vaani credentials, and a successful speak/hear turn.

## Stage 4 — Demo hardening

- [ ] Add educational disclaimers, reset control, loading states, and concise local setup instructions.
- [ ] Run the scripted chest-pain demo in a clean browser profile.
- [ ] Record known limitations and move production requirements into the next feature specification.
