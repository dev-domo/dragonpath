# DragonPath

A deadline-aware visa preparation workspace for international students in
Korea. This repo is the MVP engineering scaffold for the product defined in
`기능 정의/D-00` through `D-09` (project context, hypothesis, vision, PRD,
journey map, functional spec, UI spec).

> DragonPath is not an approval predictor. It plans deadlines, checks
> documents for missing fields, and flags cross-document inconsistencies —
> from source-backed requirements, never invented ones.

## What's in this scaffold vs. what's not

This is a working end-to-end skeleton, not the finished MVP:

**Working today**
- FastAPI backend implementing the D-08 data model (VisaCase, ChecklistItem,
  UploadedDocument, ValidationIssue, ReadinessSummary) with in-memory storage.
- The full happy-path loop: onboarding → path review → dashboard → mismatch
  resolution → completion, backed by real API calls (no mocked frontend data).
- React + TypeScript + Vite frontend implementing the 5 screens from the
  Figma file (`GDMOVvVo0Cm3Mkoy6kUdCh`, node `55:987`): Onboarding, Path
  Review, Dashboard, Mismatch Resolution (drawer), Checklist Complete.
- **Real document upload and checking.** The dashboard's "Next steps" list
  is the required-document list for the case. Every item starts pending
  (gray). Uploading a real file for an item sends it to the Upstage Studio
  document-check Agent; the item turns blue if the agent judges it
  sufficient, or red (with the agent's findings shown in a drawer) if not.
  A pending item can also be hand-confirmed without uploading anything —
  gray → blue, one-directional, never overrides a red item. See "Upstage
  Studio document-check Agent" below for a caveat about its live output.
- A "완료" (Complete) button below the checklist: gray/disabled until every
  item is blue, blue/enabled once they are, and navigates to the Checklist
  Complete screen.
- A defined contract for a *second*, separate external Upstage-based Agent
  (see "Future chat-agent integration point" below) that a teammate is
  building independently of the document-check agent above.

**Not implemented yet (see D-08/D-10 for the real scope)**
- No database — case data lives in a process-local dict and resets on
  backend restart.
- No real Rule Source Registry — `backend/app/data/seed.py` has exactly one
  demo rule (D-2-2 extension) clearly marked as placeholder data, per the
  product principle that unreviewed rules must not be presented as settled
  requirements.
- No document versioning/replace history, no delete, no auth/user accounts.
- Document classification (FS-08) is delegated entirely to the Upstage
  agent's judgment call — there's no separate schema-driven field-extraction
  step.

## Layout

```
DragonPath/
  backend/     FastAPI app (Python)
  frontend/    React + TypeScript + Vite app
```

## Running locally

**Backend** (Python 3.9+; the dev machine only has 3.9, so the codebase
avoids `X | None` syntax in favor of `typing.Optional` — feel free to
modernize this once a newer interpreter is available)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8123
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` to `http://127.0.0.1:8123`, so just
open http://localhost:5173.

## Upstage Studio document-check Agent

`backend/app/services/upstage_document_agent.py` calls the live Upstage
Studio agent (`agt_Qo9QXjejSgT6TZ3Z5MR8q2`) that powers document upload
checking: upload via `POST /v2/files`, start a job via `POST /v2/responses`,
poll `GET /v2/responses/{id}` until it completes, then parse `output_text`.

**Caveat found while wiring this up:** the documented contract for this
agent is a JSON object `{"result": bool, "How to fix": string}`, but the
currently deployed Studio agent (confirmed with both the default config and
`config_id: "1"`) actually returns a free-form Korean markdown review
instead. Rather than guess a pass/fail out of that prose — which would let
DragonPath silently invent confidence it doesn't have, exactly what D-08's
safety rules warn against — `_parse_output` in that file does this:

1. If `output_text` parses as the documented `{result, How to fix}` object,
   use it directly.
2. Otherwise, treat the response as `needs_review` (red) and surface the
   agent's full analysis as the explanation, so the user still gets real,
   specific feedback instead of a generic message.

If the Studio agent's prompt/config is later changed to emit the documented
JSON shape, path 1 picks it up automatically — no code change needed. Until
then, uploads will rarely show "blue/passed" from the agent alone; the
manual gray→blue check is the practical way to move a pending item forward
in the meantime.

`UPSTAGE_API_KEY` lives in `backend/.env` (gitignored) — a working dev key
was provided during setup; rotate it before any shared/production use.

## Future chat-agent integration point

This is unrelated to the document-check agent above. `backend/app/services/
agent_client.py` defines a minimal contract for a *separate* chat agent a
teammate is building independently:

- `POST {AGENT_BASE_URL}/chat` with `{"case_id": ..., "messages": [{"role":
  "user"|"assistant"|"system", "content": "..."}]}`
- expects back `{"reply": "..."}`

`GET /api/agent/status` reports whether it's configured; `POST /api/agent/chat`
proxies to it and returns `503` with a clear message if `AGENT_BASE_URL`
isn't set yet. Once that agent is deployed, set `AGENT_BASE_URL` /
`AGENT_API_KEY` in `backend/.env`, and adjust `AgentClient.send_message` if
its actual request/response shape differs.

## Deployment

The app runs as a single service: a multi-stage `Dockerfile` (repo root)
builds the React app, then copies it into the FastAPI container, which
serves both the API (`/api/*`) and the static app (everything else, with a
SPA fallback to `index.html` — see the bottom of `backend/app/main.py`).
One origin, no CORS to configure, no separate frontend host.

Live URL, once deployed: see the Render dashboard, or `render.yaml`'s
service name (`dragonpath`) plus your Render account's default domain
suffix (`https://dragonpath-<random>.onrender.com` unless renamed).

### One-time setup (do this yourself — account/billing can't be automated)

1. Sign up at [render.com](https://render.com) (free, no card required for
   the free plan).
2. **New > Blueprint**, point it at this GitHub repo. Render reads
   `render.yaml` and creates the `dragonpath` web service from the
   Dockerfile automatically.
3. In the new service's **Environment** tab, add `UPSTAGE_API_KEY` (the
   blueprint deliberately leaves it blank — never commit real keys to a
   public repo).
4. Since the service was created from a Blueprint, Render exposes a
   **Sync Hook** for the whole blueprint (not a per-service Deploy Hook) —
   find it on the Blueprint's page, not the service's. Copy that URL, then
   either:
   - give it to your assistant to run `gh secret set RENDER_SYNC_HOOK_URL`, or
   - add it yourself under the repo's **Settings > Secrets and variables >
     Actions** as `RENDER_SYNC_HOOK_URL`.

### How auto-deploy works

`.github/workflows/deploy.yml` runs on every push to `main`: it first
builds the backend and frontend as a sanity check, then (only if that
passes) calls the Render Blueprint's sync hook to trigger a real deploy
(the same workflow can also be run manually from the **Actions** tab via
`workflow_dispatch`). Render's own
git auto-deploy is intentionally turned off (`autoDeployTrigger: off` in
`render.yaml`) so this workflow is the single, visible trigger — check the
**Actions** tab to see deploy status instead of only the Render dashboard.
Until the secret is set, the deploy step logs a message and exits cleanly
rather than failing the build.

### Known limitations of this deployment

- **State resets on every deploy/restart.** The in-memory `CaseStore` isn't
  a real database — pushing to `main` (or Render restarting the free-tier
  instance) wipes every visa case. Fine for a demo, not for real users yet.
- **Free-tier cold starts.** After ~15 minutes idle, Render spins the
  instance down; the next request takes ~30–50s to wake it back up.
- **No auth.** Anyone with a case's URL can open/edit it. There's no login,
  so this is only appropriate for a shared demo, not real applicant data.

## Design source

Frontend screens were implemented from the Figma file linked in the
original request (fileKey `GDMOVvVo0Cm3Mkoy6kUdCh`, node `55:987`, frames
`01/Onboarding` through `05/Checklist complete`). Design tokens (colors,
type scale) are captured in `frontend/src/styles/tokens.css`.
