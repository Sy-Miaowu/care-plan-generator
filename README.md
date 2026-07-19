# Care Plan Generator

Minimal Django MVP for generating a specialty pharmacy care plan.

This first version intentionally keeps everything simple:

- Django backend
- One HTML page
- One synchronous API: `POST /api/care-plans/`
- In-memory Python dictionary storage
- No database
- No tests
- No queue
- No worker
- No websocket
- No Controller-Service-Repository layering

## Run With Docker

From this folder:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:8000
```

## Use Real LLM Generation

Create a local `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and set:

```text
OPENAI_API_KEY=your_real_key
```

Then run:

```bash
docker compose --env-file .env up --build
```

If `OPENAI_API_KEY` is not set, the app returns a demo care plan so the frontend/backend flow still works.

## Main Files

- `careplans/views.py`: form API, in-memory storage, LLM call, demo fallback
- `careplans/templates/careplans/index.html`: minimal frontend
- `careplan_project/settings.py`: minimal Django settings
- `docker-compose.yml`: local Docker runner
- `DESIGN_DOC.md`: product and engineering design doc

