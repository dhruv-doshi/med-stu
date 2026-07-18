# AI Virtual Patient Simulator Constitution

## Core Principles

### I. Educational Safety Is Non-Negotiable

The product is a fictional clinical-training simulator, never a diagnostic or treatment service for real patients. Every active consultation and evaluation screen must identify the educational purpose. MVP cases use only authored fictional data; hidden answers remain inaccessible to learners until consultation completion.

### II. Deterministic Clinical Truth, Constrained AI Expression

Structured case data, reveal rules, investigation results, consultation state, and scoring are the source of truth. An LLM may phrase a patient response or qualitative feedback only from supplied state and case facts. It must not independently decide clinical facts, invent test values, or access a diagnosis disclosure path.

### III. Demo-Safe Vertical Slices

Each implementation stage must leave a runnable, independently demonstrable flow. The text flow precedes voice; voice is an adapter over an already working session API. Use mocks and graceful fallbacks for external services so a credentials or network problem cannot prevent the core demo.

### IV. Evidence-Based Evaluation and Test Coverage

Scores must be reproducible from an explicit rubric. Qualitative feedback must cite a transcript turn or a named missed rubric item. Unit tests cover state transitions, reveal restrictions, investigations, and scoring; one end-to-end chest-pain consultation is the golden regression path.

### V. Keep the MVP Local and Reversible

The initial milestone uses JSON case files and in-memory consultation state. Do not introduce authentication, real patient data, telephony, database infrastructure, containers, or distributed workers until the local voice demo is reliable and the relevant feature has its own approved Spec Kit artifacts.

## Development Workflow

Each feature uses GitHub Spec Kit artifacts in this order: specification, clarification/checklist where needed, implementation plan, tasks, analysis, implementation, and convergence. The `specs/001-local-vaani-mvp/` directory is the active source of truth for the first build.

Changes that affect clinical rules, voice-provider behavior, API contracts, or evaluation scoring require updates to the applicable specification and tests in the same feature.

## Governance

This constitution governs all implementation decisions. Amendments must document the reason, impact on existing artifacts, and a version bump. A plan may defer a principle only with an explicit, time-bounded exception and a fallback that preserves educational safety.

**Version**: 1.0.0 | **Ratified**: 2026-07-18 | **Last Amended**: 2026-07-18
