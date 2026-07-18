# Data Model

## Authored case

`ClinicalCase` contains: `id`, `title`, `specialty`, `difficulty`, `learning_objectives`, `patient_profile`, `presenting_complaint`, `facts`, `reveal_rules`, `red_flags`, `investigations`, `expected_differentials`, `expected_management`, and `rubric`.

Each fact has a stable identifier, display text, category, and zero or more matching intent/question tags. Each investigation has an allowed name, structured result, interpretation, and appropriateness classification.

## Consultation state

`ConsultationState` contains: `id`, `case_id`, `status`, `started_at`, `transcript`, `revealed_fact_ids`, `ordered_investigation_ids`, `differentials`, `final_diagnosis`, and `management_plan`.

State is append-only for transcript and ordered investigations. `status` transitions only from `active` to `completed`.

## Evaluation

`EvaluationReport` contains: `overall_score`, category scores for history/clinical reasoning/investigations/communication/management, `missed_items`, `unnecessary_actions`, `strengths`, `evidence`, `feedback`, and `rubric_version`.

Core scores derive deterministically from state and rubric. The LLM may fill `feedback` only after deterministic results are available and must refer to IDs in `evidence`.
