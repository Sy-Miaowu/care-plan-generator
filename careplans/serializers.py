from careplans.models import CarePlan


class CarePlanCreateRequestSerializer:
    def __init__(self, post_data):
        self.post_data = post_data

    @property
    def data(self):
        return {
            "patient_first_name": self.post_data.get("patient_first_name", "").strip(),
            "patient_last_name": self.post_data.get("patient_last_name", "").strip(),
            "dob": self.post_data.get("dob", "").strip(),
            "mrn": self.post_data.get("mrn", "").strip(),
            "referring_provider": self.post_data.get("referring_provider", "").strip(),
            "referring_provider_npi": self.post_data.get(
                "referring_provider_npi", ""
            ).strip(),
            "primary_diagnosis": self.post_data.get("primary_diagnosis", "").strip(),
            "additional_diagnoses": self.post_data.get(
                "additional_diagnoses", ""
            ).strip(),
            "medication_name": self.post_data.get("medication_name", "").strip(),
            "medication_history": self.post_data.get("medication_history", "").strip(),
            "patient_records": self.post_data.get("patient_records", "").strip(),
        }


def serialize_create_care_plan_response(care_plan_id, order_id):
    return {
        "id": str(care_plan_id),
        "order_id": str(order_id),
        "status": CarePlan.STATUS_PENDING,
        "message": "Received",
    }


def serialize_care_plan_detail(care_plan):
    return {
        "id": str(care_plan.id),
        "order_id": str(care_plan.order_id),
        "status": care_plan.status,
        "order_status": care_plan.order.status,
        "input": care_plan.input_payload(),
        "care_plan": care_plan.content,
        "created_at": care_plan.created_at.isoformat(),
    }


def serialize_care_plan_status(care_plan):
    response_data = {
        "id": str(care_plan.id),
        "status": care_plan.status,
        "content": care_plan.content
        if care_plan.status == CarePlan.STATUS_COMPLETED
        else None,
    }

    if care_plan.status == CarePlan.STATUS_FAILED:
        response_data["error"] = care_plan.content or "Care plan generation failed."

    return response_data
