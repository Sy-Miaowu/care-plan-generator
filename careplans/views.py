import logging
import os

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from careplans.models import CarePlan, Order, Patient, Provider


logger = logging.getLogger(__name__)


def index(request):
    return render(request, "careplans/index.html")


@require_POST
def create_care_plan(request):
    logger.info("Received care plan generation request")

    form_data = {
        "patient_first_name": request.POST.get("patient_first_name", "").strip(),
        "patient_last_name": request.POST.get("patient_last_name", "").strip(),
        "dob": request.POST.get("dob", "").strip(),
        "mrn": request.POST.get("mrn", "").strip(),
        "referring_provider": request.POST.get("referring_provider", "").strip(),
        "referring_provider_npi": request.POST.get("referring_provider_npi", "").strip(),
        "primary_diagnosis": request.POST.get("primary_diagnosis", "").strip(),
        "additional_diagnoses": request.POST.get("additional_diagnoses", "").strip(),
        "medication_name": request.POST.get("medication_name", "").strip(),
        "medication_history": request.POST.get("medication_history", "").strip(),
        "patient_records": request.POST.get("patient_records", "").strip(),
    }

    try:
        with transaction.atomic():
            patient, _created = Patient.objects.update_or_create(
                mrn=form_data["mrn"],
                defaults={
                    "first_name": form_data["patient_first_name"],
                    "last_name": form_data["patient_last_name"],
                    "dob": form_data["dob"],
                },
            )
            provider, _created = Provider.objects.update_or_create(
                npi=form_data["referring_provider_npi"],
                defaults={"name": form_data["referring_provider"]},
            )
            order = Order.objects.create(
                patient=patient,
                provider=provider,
                medication_name=form_data["medication_name"],
                primary_diagnosis=form_data["primary_diagnosis"],
                additional_diagnoses=form_data["additional_diagnoses"],
                medication_history=form_data["medication_history"],
                patient_records=form_data["patient_records"],
                status=Order.STATUS_PENDING,
            )
            care_plan_record = CarePlan.objects.create(
                order=order,
                status=CarePlan.STATUS_PENDING,
            )
            care_plan_id = care_plan_record.id
            order_id = order.id
            transaction.on_commit(lambda: enqueue_care_plan(care_plan_id))
    except Exception:
        logger.exception("Failed to create care plan generation request")
        return JsonResponse(
            {"error": "Care plan request failed. Please try again."},
            status=503,
        )

    return JsonResponse(
        {
            "id": str(care_plan_id),
            "order_id": str(order_id),
            "status": CarePlan.STATUS_PENDING,
            "message": "Received",
        },
        status=202,
    )


def enqueue_care_plan(care_plan_id):
    from careplans.tasks import generate_care_plan_task

    generate_care_plan_task.delay(str(care_plan_id))
    logger.info("Queued Celery care plan task for %s", care_plan_id)


def generate_care_plan(form_data, fallback_on_error=True):
    prompt = build_prompt(form_data)

    logger.info("Starting LLM care plan generation")

    if not os.environ.get("OPENAI_API_KEY"):
        logger.info("LLM skipped: OPENAI_API_KEY is not set")
        return build_demo_care_plan(form_data)

    from openai import OpenAI

    try:
        client = OpenAI()
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=prompt,
        )
        logger.info("LLM returned care plan successfully")
        return response.output_text
    except Exception as exc:
        logger.info("LLM generation failed: %s", exc)
        if not fallback_on_error:
            raise
        return build_demo_care_plan(form_data, reason=str(exc))


def build_prompt(form_data):
    return f"""
You are helping a specialty pharmacy generate a draft care plan.

Create a concise care plan for the following patient and order.

Patient:
- First name: {form_data["patient_first_name"]}
- Last name: {form_data["patient_last_name"]}
- DOB: {form_data["dob"]}
- MRN: {form_data["mrn"]}

Provider:
- Name: {form_data["referring_provider"]}
- NPI: {form_data["referring_provider_npi"]}

Clinical information:
- Primary diagnosis: {form_data["primary_diagnosis"]}
- Additional diagnoses: {form_data["additional_diagnoses"]}
- Medication: {form_data["medication_name"]}
- Medication history: {form_data["medication_history"]}
- Patient records: {form_data["patient_records"]}

Output exactly these sections:
1. Problem list
2. Goals
3. Pharmacist interventions
4. Monitoring plan

Keep it practical and readable for a pharmacist to review.
This is a draft and must be reviewed by a licensed clinician.
""".strip()


def build_demo_care_plan(form_data, reason=None):
    patient_name = (
        f"{form_data['patient_first_name']} {form_data['patient_last_name']}".strip()
        or "the patient"
    )
    medication = form_data["medication_name"] or "the prescribed medication"
    diagnosis = form_data["primary_diagnosis"] or "the documented diagnosis"
    fallback_note = "DEMO MODE: Set OPENAI_API_KEY to generate this with an LLM."

    if reason:
        fallback_note = (
            "DEMO MODE: LLM generation failed, so this fallback care plan was shown.\n"
            f"Reason: {reason}"
        )

    return f"""
{fallback_note}

1. Problem list
- {patient_name} has a primary diagnosis of {diagnosis}.
- The current order is for {medication}.
- Medication history and patient records should be reviewed by the pharmacist.

2. Goals
- Support safe and effective use of {medication}.
- Improve adherence and patient understanding of therapy.
- Identify medication-related risks during pharmacist review.

3. Pharmacist interventions
- Review medication history for duplications, interactions, and adherence concerns.
- Counsel the patient on how to take {medication} as prescribed.
- Coordinate with the referring provider if clinical concerns are found.

4. Monitoring plan
- Monitor response to therapy and any reported side effects.
- Review follow-up documentation and refill history.
- Escalate unresolved safety or adherence issues to the pharmacist or provider.
""".strip()

def get_care_plan(request, care_plan_id):
    try:
        care_plan = CarePlan.objects.select_related(
            "order",
            "order__patient",
            "order__provider",
        ).get(id=care_plan_id)
    except CarePlan.DoesNotExist:
        return JsonResponse({"error": "Care plan not found"}, status=404)

    return JsonResponse(
        {
            "id": str(care_plan.id),
            "order_id": str(care_plan.order_id),
            "status": care_plan.status,
            "order_status": care_plan.order.status,
            "input": care_plan.input_payload(),
            "care_plan": care_plan.content,
            "created_at": care_plan.created_at.isoformat(),
        }
    )
