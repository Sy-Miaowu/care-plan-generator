import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from careplans.models import CarePlan
from careplans.serializers import CarePlanCreateRequestSerializer
from careplans.serializers import serialize_care_plan_detail
from careplans.serializers import serialize_care_plan_status
from careplans.serializers import serialize_create_care_plan_response
from careplans.services import create_care_plan_request
from careplans.services import get_care_plan_by_id
from careplans.services import get_care_plan_status_by_id


logger = logging.getLogger(__name__)


def index(request):
    return render(request, "careplans/index.html")


@require_POST
def create_care_plan(request):
    logger.info("Received care plan generation request")

    serializer = CarePlanCreateRequestSerializer(request.POST)
    form_data = serializer.data

    try:
        care_plan_id, order_id = create_care_plan_request(form_data)
    except Exception:
        logger.exception("Failed to create care plan generation request")
        return JsonResponse(
            {"error": "Care plan request failed. Please try again."},
            status=503,
        )

    return JsonResponse(
        serialize_create_care_plan_response(care_plan_id, order_id),
        status=202,
    )


def get_care_plan(request, care_plan_id):
    try:
        care_plan = get_care_plan_by_id(care_plan_id)
    except CarePlan.DoesNotExist:
        return JsonResponse({"error": "Care plan not found"}, status=404)

    return JsonResponse(serialize_care_plan_detail(care_plan))


@require_GET
def get_care_plan_status(request, care_plan_id):
    try:
        care_plan = get_care_plan_status_by_id(care_plan_id)
    except CarePlan.DoesNotExist:
        return JsonResponse({"error": "Care plan not found"}, status=404)

    return JsonResponse(serialize_care_plan_status(care_plan))
