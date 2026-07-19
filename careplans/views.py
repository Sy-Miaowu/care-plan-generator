import logging
import os
import uuid

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST


logger = logging.getLogger(__name__)
CARE_PLANS = {}


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

    care_plan = generate_care_plan(form_data)
    care_plan_id = str(uuid.uuid4())
    print("care_plan_id: " + care_plan_id)

    CARE_PLANS[care_plan_id] = {
        "id": care_plan_id,
        "input": form_data,
        "care_plan": care_plan,
    }

    return JsonResponse(
        {
            "id": care_plan_id,
            "care_plan": care_plan,
        }
    )


def generate_care_plan(form_data):
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
    care_plan = CARE_PLANS.get(care_plan_id)
    if not care_plan:
        return JsonResponse({"error": "Care plan not found"}, status=404)

    return JsonResponse(care_plan)
