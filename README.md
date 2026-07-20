# Care Plan Generator

Minimal Django MVP for generating a specialty pharmacy care plan.

This first version intentionally keeps everything simple:

- Django backend
- One HTML page
- One synchronous API: `POST /api/care-plans/`
- PostgreSQL storage
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

In another terminal, create the table and load mock data:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_mock_data
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

- `careplans/models.py`: `Patient`, `Provider`, `Order`, and `CarePlan` database tables
- `careplans/views.py`: form API, database persistence, LLM call, demo fallback
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
