# HTTP API Contract

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/cases` | Return safe case-selection metadata only. |
| `POST` | `/consultations` | Create `{ case_id }` and return a safe session view. |
| `POST` | `/consultations/{id}/turns` | Submit `{ text, input_mode }`; return patient reply, revealed fact labels, and updated transcript. |
| `POST` | `/consultations/{id}/investigations` | Submit `{ investigation_id }`; return predefined result or validation error. |
| `POST` | `/consultations/{id}/differentials` | Replace/add `{ differentials }` during an active session. |
| `POST` | `/consultations/{id}/complete` | Submit `{ final_diagnosis, management_plan }`, mark completed, and return the report. |
| `GET` | `/consultations/{id}/evaluation` | Return evaluation only after completion. |
| `POST` | `/voice/sessions` | Create a Vaani or mock browser voice session without exposing provider secrets. |
| `POST` | `/consultations/{id}/vaani/webrtc` | Create a Vaani WebRTC session, map its room to the consultation, and return only short-lived LiveKit browser credentials. |

## Error rules

- Unknown case, consultation, or investigation: `404`.
- Invalid request shape or invalid status transition: `422`.
- Voice provider unavailable: a structured `503` with `fallback: "text"`; the consultation remains active.
- Hidden data is never included in any response before completion.
