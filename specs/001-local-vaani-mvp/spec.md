# Feature Specification: Local Vaani Voice MVP

**Feature Branch**: `001-local-vaani-mvp`  
**Created**: 2026-07-18  
**Status**: Ready for task implementation

## User Scenarios & Testing

### User Story 1 — Conduct a safe consultation (Priority: P1)

A medical learner selects a fictional case, asks questions by text or voice, and receives case-grounded patient replies without seeing the hidden diagnosis.

**Independent Test**: Start the chest-pain case, ask a red-flag question, and verify the allowed fact appears in the transcript while the diagnosis does not.

**Acceptance Scenarios**:

1. **Given** an unstarted case, **When** the learner starts a consultation, **Then** the app creates an active consultation with no revealed hidden facts.
2. **Given** an active consultation, **When** the learner asks an appropriate question, **Then** the patient replies only from case data and the state records the turn.
3. **Given** an active consultation, **When** the learner uses a voice-capable browser, **Then** spoken input and an audible patient response have visible transcript text.

### User Story 2 — Order and interpret fixed investigations (Priority: P1)

A learner can order a case-supported investigation and view its predefined structured result.

**Independent Test**: Order ECG in the chest-pain case and receive the authored result rather than a generated value.

### User Story 3 — Receive evidence-backed evaluation (Priority: P1)

After submitting differentials, final diagnosis, and management, a learner receives a structured score, missed items, strengths, and feedback grounded in the session transcript.

**Independent Test**: Complete the golden chest-pain fixture and compare each deterministic score and missed item with the expected result.

### User Story 4 — Choose among five cases (Priority: P2)

A learner can select chest pain, diabetes follow-up, migraine, upper respiratory infection, or abdominal pain from one case-selection screen.

**Independent Test**: Start and complete a smoke consultation for every case using its own authored investigation results and rubric.

## Edge Cases

- Vaani access, microphone permission, or network access fails: retain the text consultation and show an actionable non-blocking message.
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
- **FR-008**: The system MUST expose a `VoiceProvider` adapter with a Vaani implementation and a no-credential mock/text fallback.
- **FR-009**: The system MUST display the transcript for both typed and voice interactions.
- **FR-010**: The system MUST prevent active consultations from exposing the hidden diagnosis or answer rubric to the browser.

## Success Criteria

- **SC-001**: A clean local setup can run a complete chest-pain consultation and evaluation within five minutes of starting the application.
- **SC-002**: The scripted chest-pain demo completes in under two minutes without manual data editing.
- **SC-003**: Automated tests pass for all clinical-state transitions and the chest-pain golden evaluation.
- **SC-004**: Each of the five cases can be started, questioned, investigated, and completed in a smoke test.
- **SC-005**: A Vaani failure never prevents the learner from finishing the text demo.

## Assumptions

- Vaani Labs is the default voice target, using its browser-capable session API after account credentials are supplied.
- A structured-output LLM key will be supplied in the local environment; no model provider is hard-coded into clinical logic.
- The two-hour build target excludes user accounts, durable storage, Docker, telephony, and online deployment.
