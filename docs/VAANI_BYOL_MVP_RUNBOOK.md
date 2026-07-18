# Vaani BYOL Virtual Patient MVP Runbook

This guide configures the MVP as a real phone-call consultation. Vaani handles live STT, TTS, audio media, and turn-taking. The web browser displays the live transcript, ordered reports, and final evaluation. FastAPI remains the trusted clinical-simulation backend.

## 1. What you will build

1. Select a fictional case in the browser.
2. Enter the learner’s phone number in E.164 form, for example `+919876543210`.
3. FastAPI dispatches a Vaani call to that number.
4. The learner speaks naturally, including interrupting the patient.
5. Vaani sends completed learner turns to the FastAPI BYOL WebSocket.
6. FastAPI updates the case state, streams the safe patient reply back to Vaani, and pushes transcript/report events to the browser.
7. Vaani sends a final lifecycle webhook when the call ends; FastAPI runs evaluation and the browser renders it.

## 2. Prerequisites

- Vaani Voice account, API key, and funded/provisioned test phone number.
- OpenRouter API key and a model that supports JSON output.
- A phone capable of receiving the Vaani test call.
- Node 22+, Python 3.11+, `uv`, and npm installed locally.
- For the deployed path below, a Railway or Render account. For an entirely local test, a public HTTPS/WSS tunnel is still required because Vaani cannot reach `localhost` directly.

## 3. Configure Vaani dashboard

### Create the patient voice agent

1. Open **Agent Config → Create Agent**.
2. Name it `virtual-patient-mvp`.
3. Select `en-IN` and a conversational adult voice.
4. Keep the static prompt short. It must state that this is a fictional educational patient and that all clinical replies come from the BYOL server. Do not put a diagnosis or a complete case in this prompt.
5. Save and copy the UUID `agent_id`.

### Enable BYOL

1. Open the new agent.
2. Go to **Brain → Reasoning Language Model (LLM) → Bring Your Own LLM**.
3. Set the URL to `wss://<your-public-domain>/vaani/byol`.
4. Click **Test Connection** after the backend and tunnel are running.
5. Select **No fallback**. This is mandatory: a platform fallback could generate an ungrounded patient response.
6. Save the configuration.

### Configure telephony and webhook

1. Go to **Settings → Telephony**, provision a test number, and assign it to the Vaani agent.
2. Go to **Settings → Webhooks** and add `https://<your-public-domain>/vaani/webhook`.
3. Subscribe to `call_started`, `user_picked_up_at`, `call_ended`, and `call_postprocessing`.
4. If the dashboard provides a webhook signing secret, add it to `.env` and enable signature verification before deployment.

## 4. Local environment

Create `.env` from `.env.example` and set server-only values:

```dotenv
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=...
VAANI_API_KEY=...
VAANI_AGENT_ID=<agent UUID from dashboard>
VAANI_WEBHOOK_SECRET=<optional signing secret>
PUBLIC_BASE_URL=https://<your-public-domain>
CORS_ORIGINS=http://localhost:3000
```

Never commit `.env`, paste secrets into a chat, or add Vaani/OpenRouter keys to `NEXT_PUBLIC_*` variables.

## 5. Start local services and tunnel

Open three terminals at the repository root.

```bash
./scripts/run-backend.sh
```

```bash
./scripts/run-frontend.sh
```

Expose the FastAPI port with your tunnel provider. Example pattern:

```bash
ngrok http 8000
```

Copy the generated `https://...` address into `PUBLIC_BASE_URL`; convert it to `wss://...` for the BYOL setting. Restart FastAPI after changing `.env`.

### Free browser-live demo (no phone number, telephony, Vaani setup, or tunnel)

For the fastest zero-cost demonstration, keep only the backend and frontend
running, then open `http://localhost:3000` in Chrome.

1. Select **Acute chest pain**.
2. Select **Start browser live demo** and grant microphone permission.
3. Speak a history question. The transcript and browser-spoken patient reply appear in the page.
4. Speak while the patient reply is playing to cancel browser TTS, then ask the next question.
5. Say “Please order an ECG.” The authored ECG report appears in the reports panel.
6. Select **Complete consultation** to generate the evaluation without waiting for a Vaani webhook.

Use headphones. The browser Web Speech APIs are free and preserve the
case-safe backend flow, but they are not Vaani/WebRTC and therefore cannot
guarantee telephony-quality barge-in on every browser. Chrome is recommended.

## 6. Fastest hosted MVP: one Railway or Render service

The repository now includes a `Dockerfile` that builds the Next.js frontend as
static files and serves it from FastAPI. This means the browser, REST API,
browser WebSocket, Vaani BYOL WebSocket, and Vaani webhook all use one public
domain. Normal browser CORS is not needed in this layout.

### Railway deployment

1. The deployment source is `https://github.com/dhruv-doshi/med-stu.git`, branch `main`.
2. In Railway, create **New Project → Deploy from GitHub Repo** and select `dhruv-doshi/med-stu`.
3. Choose the `main` branch. Railway detects the root `Dockerfile`; leave the root directory as the repository root. Do not set a custom build command or start command.
4. Wait for the first build to finish, then go to **Settings → Networking** and generate a public domain. Copy its complete `https://...` address.
5. In the service's **Variables** panel, add these values. Replace every placeholder before pressing Deploy:

```dotenv
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=openai/gpt-4o-mini
VAANI_API_KEY=...
VAANI_AGENT_ID=<Vaani agent UUID>
VAANI_API_BASE_URL=https://api.vaanivoice.ai
PUBLIC_BASE_URL=https://<your-actual-railway-domain>
CORS_ORIGINS=https://<your-actual-railway-domain>
```

6. Redeploy after saving variables. Open `https://<your-actual-railway-domain>/health`. It must return
   `{"status":"ok"}`.
7. Open the same domain without `/health`. The virtual-patient browser UI must load. This is the only browser URL you need; do not deploy the `frontend/` directory separately.

### Render deployment

1. Create a **Web Service** from the GitHub repository.
2. Choose **Docker** as the runtime and leave the root directory as the repository root.
3. Add exactly the environment variables shown in the Railway section, substituting the Render public domain for `PUBLIC_BASE_URL` and `CORS_ORIGINS`.
4. Deploy, then verify `/health` and the root browser UI.

### Vaani settings for either host

After the public domain is working, configure Vaani with the exact same host:

```text
BYOL URL:  wss://<public-domain>/vaani/byol
Webhook:   https://<public-domain>/vaani/webhook
Fallback:  No fallback
```

In Vaani, complete the dashboard setup in this order:

1. Create one agent named `virtual-patient-mvp`, select an `en-IN` conversational voice, and copy its UUID into Railway as `VAANI_AGENT_ID`.
2. In **Brain → Reasoning Language Model**, select **Bring Your Own LLM** and paste the `wss://.../vaani/byol` URL above. Click **Test Connection**; it must succeed before making a call.
3. Set the platform fallback to **No fallback**, then save the agent.
4. Provision or select a Vaani test number, assign it to the agent, and ensure it is permitted to call the learner phone number.
5. In Vaani webhooks, add the `https://.../vaani/webhook` URL above and subscribe to `call_started`, `user_picked_up_at`, `call_ended`, and `call_postprocessing`.
6. Return to the deployed browser app, choose a case, enter a reachable E.164 phone number such as `+9198...`, and select **Start Vaani call**.

### Human-only deployment checklist

- [ ] Railway GitHub integration is authorized and the `main` branch is selected.
- [ ] Railway public domain is generated and copied exactly into `PUBLIC_BASE_URL`.
- [ ] Vaani/OpenRouter credentials are entered in Railway Variables; none are committed to Git.
- [ ] Vaani BYOL Test Connection succeeds with the Railway WSS URL.
- [ ] A Vaani phone number is assigned and can call the chosen test phone.
- [ ] The webhook events are subscribed and the chest-pain call completes once.

Do not set `NEXT_PUBLIC_API_BASE_URL` for this single-service Docker deployment.
The frontend is built to call its own origin, so it automatically uses the same
HTTPS/WSS domain as FastAPI. Never add the Vaani or OpenRouter keys as
`NEXT_PUBLIC_*` variables.

## 7. BYOL protocol contract

Vaani opens one WebSocket per call and appends its call ID to the configured BYOL path. On connection, FastAPI sends these frames in order:

```json
{"interaction_type":"config","content":"Server ready"}
{"interaction_type":"greeting","content":"Hello"}
```

For each learner turn, Vaani sends `response_required` with a `response_id` and full transcript. FastAPI must stream one or more response frames with the same ID:

```json
{"response_type":"response","response_id":7,"content":"The pain has been constant since it began.","content_complete":false}
{"response_type":"response","response_id":7,"content":"","content_complete":true}
```

The backend maps Vaani’s call ID to the active consultation created by the browser. It never trusts a caller-provided case ID on the BYOL connection.

## 8. Live browser events

The browser connects to `/consultations/{consultation_id}/live`. It renders events in arrival order:

- `call_status`: dispatching, ringing, active, ended, degraded.
- `transcript_turn`: learner or patient text.
- `investigation_ordered`: show a pending report card.
- `investigation_result`: reveal the authored structured result.
- `evaluation_ready`: navigate to or render the evaluation panel.

When the learner says “Order ECG and troponin”, the action extractor returns allowed investigation IDs. The deterministic case engine validates them, stores the order, and emits browser events. Do not generate values with an LLM.

## 9. Interruption and continuous conversation

Vaani is the audio authority. Its voice-agent runtime detects the learner speaking while the patient is talking and controls the active TTS/STT turn. The backend must treat Vaani’s newest `response_required` message as authoritative:

1. Cancel any unfinished OpenRouter generation for the prior response ID.
2. Do not send remaining chunks from that abandoned turn.
3. Process the newest turn using current clinical state.
4. Stream the new answer with the new response ID.

Test this explicitly: while the patient is speaking, interrupt with “Has it ever happened before?” Confirm patient audio stops, no old chunks continue, and the browser shows the new learner turn.

## 10. First hosted demo script

1. Open `https://<public-domain>` and select Acute chest pain.
2. Enter the learner's E.164 phone number and dispatch the Vaani call.
3. Ask about onset, constant nature, radiation, sweating, smoking, and breathlessness.
4. Interrupt the patient once to confirm natural barge-in.
5. Say: “Order ECG and troponin.” Watch both report cards appear in the browser.
6. State acute coronary syndrome and a management plan.
7. End the call.
8. Wait for Vaani `call_postprocessing`; confirm the evaluation report appears with transcript evidence.

## 11. Troubleshooting

| Symptom | Check |
|---|---|
| BYOL test connection fails | Backend is running, tunnel is HTTPS/WSS, BYOL URL has no local hostname, and tunnel points to port 8000. |
| Vaani falls back or hallucinates | Set BYOL fallback to **No fallback** and verify backend WebSocket responses. |
| Browser has no live transcript | Confirm consultation-to-call mapping and browser live WebSocket connection. |
| No investigation appears | Inspect action-extractor JSON and case investigation IDs; never bypass State Engine validation. |
| Duplicate evaluation | Make webhook handling idempotent by call ID and event type. |
| Interrupted reply continues | Cancel the prior generation task and stop emitting chunks when the next response ID arrives. |
| Browser UI returns a 404 | Confirm the Docker build completed and the service is deploying from the repository root, not `frontend/` or `backend/`. |
| API works but Vaani cannot connect | Use the generated public domain, verify `wss://` rather than `https://` for BYOL, and redeploy after updating `PUBLIC_BASE_URL`. |

## 12. MVP completion checklist

- [ ] Vaani agent created, BYOL enabled, no fallback selected.
- [ ] Telephony number assigned and webhook registered.
- [ ] Local WSS endpoint passes Vaani Test Connection.
- [ ] Browser launches a call and shows live status/transcript.
- [ ] Spoken ECG order appears in browser with predefined result.
- [ ] Learner interruption does not produce overlapping responses.
- [ ] Call end triggers a single evaluation report.
- [ ] All backend and frontend tests pass.
