# Care Plan Generator

Minimal Django MVP for generating a specialty pharmacy care plan.

This first version intentionally keeps everything simple:

- Django backend
- One HTML page
- One asynchronous submit API: `POST /api/care-plans/`
- PostgreSQL storage
- Redis-backed Celery task queue
- Celery worker for background care plan generation
- No tests
- No websocket
- No Controller-Service-Repository layering

## Run With Docker

From this folder:

```bash
docker compose up --build
```

In another terminal, create the table and load mock data:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_mock_data
```

Then open:

```text
http://localhost:8000
```

## LLM Configuration

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

The submit API does not call the LLM directly. The Celery worker consumes queued care plan jobs and calls the LLM in the background.

## Current Async Flow

`POST /api/care-plans/` now:

1. Persists the patient, provider, `Order(status="pending")`, and `CarePlan(status="pending")`.
2. Queues a Celery task with the `care_plan_id`.
3. Returns `202 Accepted` with `message`, `id`, `order_id`, and `status`.

The Celery worker:

1. Receives the `care_plan_id` from Redis.
2. Marks the matching `Order` and `CarePlan` as `processing`.
3. Calls the LLM care plan generator.
4. Saves the generated content and marks the `Order` and `CarePlan` as `completed`.
5. Retries failures up to 3 times with exponential backoff.

The frontend intentionally does not receive an automatic update. Refresh or manually fetch the care plan later to see the completed result.

## Main Files

- `careplans/models.py`: `Patient`, `Provider`, `Order`, and `CarePlan` database tables
- `careplans/views.py`: form API, database persistence, Celery enqueue, LLM helper
- `careplans/tasks.py`: Celery task for background care plan generation
- `careplan_project/celery.py`: Celery app configuration
- `careplans/templates/careplans/index.html`: minimal frontend
- `careplan_project/settings.py`: minimal Django settings
- `docker-compose.yml`: local Docker runner
- `DESIGN_DOC.md`: product and engineering design doc

## Load Mock Data For TablePlus

Start PostgreSQL:

```bash
docker compose up -d db
```

Connect from TablePlus:

```text
Host: localhost
Port: 5432
Database: careplans
User: careplans
Password: careplans_dev_password
```

Then create the tables and load five sample care plans with Django:

```bash
python manage.py migrate
python manage.py seed_mock_data
```

Or run this PostgreSQL SQL file in TablePlus:

```text
scripts/import_mock_data_postgres.sql
```

The main tables are:

```text
careplans_patient
careplans_provider
careplans_order
careplans_careplan
```

Relationships:

```text
careplans_patient.mrn   -> careplans_order.patient_mrn
careplans_provider.npi  -> careplans_order.provider_npi
careplans_order.id      -> careplans_careplan.order_id
```
