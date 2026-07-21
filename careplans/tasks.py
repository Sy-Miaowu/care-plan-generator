import logging

from celery import shared_task
from django.db import transaction

from careplans.models import CarePlan, Order
from careplans.views import generate_care_plan


logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_care_plan_task(self, care_plan_id):
    logger.info("Celery task started for care plan %s", care_plan_id)

    try:
        with transaction.atomic():
            care_plan = (
                CarePlan.objects.select_for_update()
                .select_related("order", "order__patient", "order__provider")
                .get(id=care_plan_id)
            )

            if care_plan.status == CarePlan.STATUS_COMPLETED:
                logger.info("Care plan %s is already completed; skipping", care_plan_id)
                return

            care_plan.status = CarePlan.STATUS_PROCESSING
            care_plan.save(update_fields=["status", "updated_at"])
            care_plan.order.status = Order.STATUS_PROCESSING
            care_plan.order.save(update_fields=["status", "updated_at"])

        generated_content = generate_care_plan(
            care_plan.input_payload(),
            fallback_on_error=False,
        )

        care_plan.content = generated_content
        care_plan.status = CarePlan.STATUS_COMPLETED
        care_plan.save(update_fields=["content", "status", "updated_at"])
        care_plan.order.status = Order.STATUS_COMPLETED
        care_plan.order.save(update_fields=["status", "updated_at"])
        logger.info("Celery task completed for care plan %s", care_plan_id)
    except CarePlan.DoesNotExist:
        logger.exception("Care plan %s does not exist", care_plan_id)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            logger.exception("Care plan %s failed after retries", care_plan_id)
            CarePlan.objects.filter(id=care_plan_id).update(
                status=CarePlan.STATUS_FAILED,
                content=f"Care plan generation failed: {exc}",
            )
            Order.objects.filter(care_plan__id=care_plan_id).update(
                status=Order.STATUS_FAILED,
            )
            raise

        countdown = 2**self.request.retries
        logger.warning(
            "Care plan %s failed; retrying in %s seconds",
            care_plan_id,
            countdown,
        )
        raise self.retry(exc=exc, countdown=countdown)
