# Feature Specification: Local Vaani Voice MVP

**Feature Branch**: `001-local-vaani-mvp`  
**Created**: 2026-07-18  
**Status**: Revised for Vaani BYOL implementation

## User Scenarios & Testing

### User Story 1 — Conduct a safe consultation (Priority: P1)

A medical learner selects a fictional case, asks questions by text or voice, and receives case-grounded patient replies without seeing the hidden diagnosis.

**Independent Test**: Start the chest-pain case, ask a red-flag question, and verify the allowed fact appears in the transcript while the diagnosis does not.

**Acceptance Scenarios**:

1. **Given** an unstarted case, **When** the learner starts a consultation, **Then** the app creates an active consultation with no revealed hidden facts.
2. **Given** an active consultation, **When** the learner asks an appropriate question, **Then** the patient replies only from case data and the state records the turn.
3. **Given** an active phone consultation, **When** the learner speaks or interrupts the patient, **Then** Vaani owns live STT/TTS turn-taking and the browser receives transcript/status updates.

### User Story 2 — Order and interpret fixed investigations (Priority: P1)

A learner can order a case-supported investigation and view its predefined structured result.

**Independent Test**: Order ECG in the chest-pain case and receive the authored result rather than a generated value.

### User Story 3 — Receive evidence-backed evaluation (Priority: P1)

After submitting differentials, final diagnosis, and management, a learner receives a structured score, missed items, strengths, and feedback grounded in the session transcript.

**Independent Test**: Complete the golden chest-pain fixture and compare each deterministic score and missed item with the expected result.

### User Story 4 — Choose among five cases (Priority: P2)

A learner can select chest pain, diabetes follow-up, migraine, upper respiratory infection, or abdominal pain from one case-selection screen.

**Independent Test**: Start and complete a smoke consultation for every case using its own authored investigation results and rubric.

### User Story 5 — Monitor a live voice call (Priority: P1)

A learner starts a Vaani phone consultation from the browser and watches the transcript, ordered investigations, and results update without refreshing the page.

**Independent Test**: Start a chest-pain call, verbally order ECG, and observe the order/result appear in the browser before the call ends.

## Edge Cases

- Vaani BYOL WebSocket fails: use no platform-LLM fallback, mark the call degraded, and preserve browser text mode for recovery.
- The learner asks an unclear or unsupported question: the patient asks for clarification and does not invent facts.
- The learner repeats a question: the patient may restate the already revealed fact consistently.
- An unknown investigation is requested: reject it without altering consultation state.
- Completion without a final diagnosis: return an incomplete evaluation with explicit missing-submission feedback.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST prominently label each consultation and evaluation as a fictional educational simulation.
- **FR-002**: The system MUST load five authored cases from a shared versioned JSON schema.
- **FR-003**: The system MUST keep diagnosis, facts, reveal rules, investigations, and rubric data server-side during an active consultation.
- **FR-004**: The system MUST persist all active-session turns, revealed facts, orders, differentials, and submissions in a single consultation state object.
- **FR-005**: The system MUST return only predefined investigation results.
- **FR-006**: The system MUST calculate core scores deterministically and return structured evaluation JSON.
- **FR-007**: The system MUST use an LLM only through a constrained patient-response/feedback interface supplied with case-safe context.
- **FR-008**: The system MUST dispatch a Vaani Voice agent call using a configured `agent_id` and map the returned call ID to the consultation.
- **FR-009**: The system MUST implement Vaani BYOL’s persistent WebSocket protocol and stream Patient Agent text chunks back to Vaani.
- **FR-010**: The browser MUST subscribe to a consultation-specific WebSocket for transcript, call-status, investigation, and evaluation events.
- **FR-011**: A spoken investigation order MUST be extracted into structured action JSON, validated by deterministic case rules, and broadcast to the browser.
- **FR-012**: The Vaani agent MUST use no platform-LLM fallback; only the constrained backend Patient Agent may formulate patient content.
- **FR-013**: The system MUST prevent active consultations from exposing the hidden diagnosis or answer rubric to the browser.

## Success Criteria

- **SC-001**: A clean local setup can run a complete chest-pain consultation and evaluation within five minutes of starting the application.
- **SC-002**: The scripted chest-pain demo completes in under two minutes without manual data editing.
- **SC-003**: Automated tests pass for all clinical-state transitions and the chest-pain golden evaluation.
- **SC-004**: Each of the five cases can be started, questioned, investigated, and completed in a smoke test.
- **SC-005**: A spoken ECG order appears in the live browser dashboard before the call ends.
- **SC-006**: A test call can be interrupted naturally by the learner without the backend emitting a second patient response for the abandoned turn.

## Assumptions

- Vaani Voice (`docs.vaanivoice.ai`) is the default voice target, using a phone-call agent with BYOL enabled.
- A structured-output LLM key will be supplied in the local environment; no model provider is hard-coded into clinical logic.
- The local demo exposes the BYOL WebSocket through a temporary HTTPS/WSS tunnel; production deployment is deferred.
