# AI Virtual Patient Simulator Roadmap

## Phase 0 — Spec Kit foundation

Create and maintain the constitution plus the `001-local-vaani-mvp` specification, plan, task list, API contract, data model, and demo script.

## Phase 1 — Local text vertical slice

Deliver case selection, a deterministic text consultation, structured investigations, final submission, and evaluation for the chest-pain golden path.

## Phase 2 — Five-case evaluation MVP

Add diabetes follow-up, migraine, upper respiratory infection, and abdominal pain using the common case schema. Add per-case rubric data and regression fixtures.

## Phase 3 — Local Vaani voice demo

Add microphone input, speech transcription, spoken patient replies, and transcript display through the Vaani provider adapter. Preserve the text fallback and app-owned clinical state.

## Phase 4 — Demo hardening

Improve loading, permission, and provider-failure states; rehearse the scripted chest-pain demo; document local setup and known limitations.

## Phase 5 — Online scale-up (deferred)

Replace in-memory state with durable storage; add authentication, container deployment, observability, rate limits, background jobs, provider resilience, security/privacy controls, analytics, faculty authoring, and production voice reliability.
