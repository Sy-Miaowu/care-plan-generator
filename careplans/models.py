import uuid

from django.db import models


class Patient(models.Model):
    mrn = models.CharField(max_length=50, primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.mrn})"


class Provider(models.Model):
    npi = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.npi})"


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="orders",
        db_column="patient_mrn",
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="orders",
        db_column="provider_npi",
    )
    medication_name = models.CharField(max_length=150)
    primary_diagnosis = models.CharField(max_length=255)
    additional_diagnoses = models.TextField(blank=True)
    medication_history = models.TextField(blank=True)
    patient_records = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.medication_name} for {self.patient}"


class CarePlan(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_FAILED, "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="care_plan")
    content = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Care plan for order {self.order_id} ({self.status})"

    def input_payload(self):
        order = self.order
        patient = order.patient
        provider = order.provider

        return {
            "patient_first_name": patient.first_name,
            "patient_last_name": patient.last_name,
            "dob": patient.dob.isoformat(),
            "mrn": patient.mrn,
            "referring_provider": provider.name,
            "referring_provider_npi": provider.npi,
            "primary_diagnosis": order.primary_diagnosis,
            "additional_diagnoses": order.additional_diagnoses,
            "medication_name": order.medication_name,
            "medication_history": order.medication_history,
            "patient_records": order.patient_records,
        }
