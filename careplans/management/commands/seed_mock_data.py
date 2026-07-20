from django.core.management.base import BaseCommand

from careplans.models import CarePlan, Order, Patient, Provider


MOCK_CARE_PLANS = [
    {
        "patient": {
            "first_name": "Jane",
            "last_name": "Doe",
            "mrn": "MRN-100001",
            "dob": "1975-04-12",
        },
        "provider": {
            "name": "Dr. Amanda Smith",
            "npi": "1234567890",
        },
        "order": {
            "id": "11111111-1111-4111-8111-111111111301",
            "medication_name": "Humira",
            "primary_diagnosis": "M06.9 Rheumatoid arthritis, unspecified",
            "additional_diagnoses": "I10 Essential hypertension; E11.9 Type 2 diabetes mellitus without complications",
            "medication_history": "Methotrexate 15 mg weekly; folic acid 1 mg daily; ibuprofen as needed.",
            "patient_records": "Persistent joint pain and morning stiffness despite methotrexate. No known latex allergy. TB screening negative.",
        },
        "care_plan": {
            "id": "11111111-1111-4111-8111-111111111401",
            "status": CarePlan.STATUS_COMPLETED,
            "content": "1. Problem list\n- Rheumatoid arthritis with ongoing symptoms.\n- Starting Humira therapy.\n- Comorbid hypertension and type 2 diabetes require routine monitoring.\n\n2. Goals\n- Reduce joint pain and morning stiffness.\n- Support safe initiation and adherence to Humira.\n- Identify infection risks early.\n\n3. Pharmacist interventions\n- Confirm TB/hepatitis screening and vaccination history.\n- Counsel on injection technique, storage, missed doses, and infection warning signs.\n- Review medication list for duplicate immunosuppressive therapy.\n\n4. Monitoring plan\n- Reassess symptom response and adverse effects after 8 to 12 weeks.\n- Monitor refill history and injection confidence.\n- Escalate fever, recurrent infection, or severe injection-site reaction.",
        },
    },
    {
        "patient": {
            "first_name": "Michael",
            "last_name": "Chen",
            "mrn": "MRN-100002",
            "dob": "1988-09-03",
        },
        "provider": {
            "name": "Dr. Priya Patel",
            "npi": "1987654321",
        },
        "order": {
            "id": "22222222-2222-4222-8222-222222222301",
            "medication_name": "Stelara",
            "primary_diagnosis": "L40.0 Psoriasis vulgaris",
            "additional_diagnoses": "E78.5 Hyperlipidemia",
            "medication_history": "Topical clobetasol; phototherapy trial with partial response.",
            "patient_records": "Moderate plaque psoriasis affecting elbows, knees, and scalp. Patient reports embarrassment and itching impacting sleep.",
        },
        "care_plan": {
            "id": "22222222-2222-4222-8222-222222222401",
            "status": CarePlan.STATUS_COMPLETED,
            "content": "1. Problem list\n- Moderate plaque psoriasis with incomplete response to topical therapy and phototherapy.\n- New Stelara order requires dosing schedule education.\n\n2. Goals\n- Improve plaque clearance and itching.\n- Promote correct injection timing and adherence.\n- Minimize infection and hypersensitivity risk.\n\n3. Pharmacist interventions\n- Verify weight-based dose and induction/maintenance schedule.\n- Counsel on storage, administration, missed doses, and infection precautions.\n- Coordinate prior authorization and copay support if needed.\n\n4. Monitoring plan\n- Follow up before the next scheduled dose to confirm adherence.\n- Track skin symptoms, itching, sleep impact, and adverse effects.\n- Notify provider if symptoms worsen or infection signs occur.",
        },
    },
    {
        "patient": {
            "first_name": "Elena",
            "last_name": "Garcia",
            "mrn": "MRN-100003",
            "dob": "1966-01-27",
        },
        "provider": {
            "name": "Dr. Robert Lee",
            "npi": "1098765432",
        },
        "order": {
            "id": "33333333-3333-4333-8333-333333333301",
            "medication_name": "Dupixent",
            "primary_diagnosis": "J45.50 Severe persistent asthma, uncomplicated",
            "additional_diagnoses": "J30.9 Allergic rhinitis, unspecified",
            "medication_history": "High-dose inhaled corticosteroid/LABA; albuterol rescue inhaler; montelukast.",
            "patient_records": "Three exacerbations in the past year requiring oral steroids. Reports nighttime symptoms twice weekly.",
        },
        "care_plan": {
            "id": "33333333-3333-4333-8333-333333333401",
            "status": CarePlan.STATUS_COMPLETED,
            "content": "1. Problem list\n- Severe persistent asthma with recent steroid-requiring exacerbations.\n- Starting Dupixent add-on therapy.\n- Rescue inhaler use and nighttime symptoms require monitoring.\n\n2. Goals\n- Reduce exacerbation frequency and nighttime symptoms.\n- Improve adherence to maintenance therapy.\n- Support safe self-administration.\n\n3. Pharmacist interventions\n- Review injection training and dosing cadence.\n- Reinforce that Dupixent is not a rescue medication.\n- Confirm patient continues controller inhaler unless provider changes regimen.\n\n4. Monitoring plan\n- Track exacerbations, rescue inhaler use, and missed doses monthly.\n- Monitor injection-site reactions, eye symptoms, and allergic reactions.\n- Escalate worsening breathing symptoms or frequent albuterol use.",
        },
    },
    {
        "patient": {
            "first_name": "Robert",
            "last_name": "Johnson",
            "mrn": "MRN-100004",
            "dob": "1959-11-18",
        },
        "provider": {
            "name": "Dr. Sarah Nguyen",
            "npi": "1456789012",
        },
        "order": {
            "id": "44444444-4444-4444-8444-444444444301",
            "medication_name": "Ocrevus",
            "primary_diagnosis": "G35 Multiple sclerosis",
            "additional_diagnoses": "R53.83 Other fatigue",
            "medication_history": "Previously on glatiramer acetate; discontinued due to breakthrough relapse.",
            "patient_records": "Relapsing symptoms with new MRI lesions. Hepatitis B screening completed per clinic note.",
        },
        "care_plan": {
            "id": "44444444-4444-4444-8444-444444444401",
            "status": CarePlan.STATUS_COMPLETED,
            "content": "1. Problem list\n- Multiple sclerosis with breakthrough disease activity on prior therapy.\n- New Ocrevus infusion requires safety coordination.\n\n2. Goals\n- Reduce relapse risk and new lesion activity.\n- Prepare patient for infusion schedule and potential reactions.\n- Maintain safety monitoring around immunosuppression.\n\n3. Pharmacist interventions\n- Confirm hepatitis B screening and premedication plan.\n- Counsel on infusion reactions and infection precautions.\n- Coordinate infusion appointment readiness and medication access.\n\n4. Monitoring plan\n- Monitor infusion tolerance and delayed reactions.\n- Track infection symptoms and neurologic changes.\n- Follow refill/infusion schedule and provider follow-up notes.",
        },
    },
    {
        "patient": {
            "first_name": "Aisha",
            "last_name": "Williams",
            "mrn": "MRN-100005",
            "dob": "1994-06-21",
        },
        "provider": {
            "name": "Dr. Karen Brown",
            "npi": "1765432109",
        },
        "order": {
            "id": "55555555-5555-4555-8555-555555555301",
            "medication_name": "Skyrizi",
            "primary_diagnosis": "K50.90 Crohn's disease, unspecified, without complications",
            "additional_diagnoses": "D50.9 Iron deficiency anemia, unspecified",
            "medication_history": "Prednisone taper; mesalamine; prior infliximab loss of response.",
            "patient_records": "Reports abdominal pain, loose stools, and fatigue. Recent labs show low ferritin. No active infection documented.",
        },
        "care_plan": {
            "id": "55555555-5555-4555-8555-555555555401",
            "status": CarePlan.STATUS_COMPLETED,
            "content": "1. Problem list\n- Crohn's disease symptoms after loss of response to prior biologic.\n- Iron deficiency anemia and fatigue noted in records.\n- Starting Skyrizi therapy.\n\n2. Goals\n- Reduce gastrointestinal symptoms and improve quality of life.\n- Support adherence through induction and maintenance phases.\n- Identify infection or hypersensitivity concerns early.\n\n3. Pharmacist interventions\n- Review induction-to-maintenance transition and dosing calendar.\n- Counsel on storage, administration, missed doses, and side effects.\n- Coordinate with provider regarding anemia follow-up if not already planned.\n\n4. Monitoring plan\n- Track stool frequency, abdominal pain, fatigue, and weight changes.\n- Monitor adherence, adverse effects, and signs of infection.\n- Escalate severe abdominal pain, fever, or persistent worsening symptoms.",
        },
    },
]


class Command(BaseCommand):
    help = "Load mock patients, providers, orders, and care plans."

    def handle(self, *args, **options):
        for item in MOCK_CARE_PLANS:
            patient_data = item["patient"]
            provider_data = item["provider"]
            order_data = item["order"]
            care_plan_data = item["care_plan"]

            patient, _created = Patient.objects.update_or_create(
                mrn=patient_data["mrn"],
                defaults=patient_data,
            )
            provider, _created = Provider.objects.update_or_create(
                npi=provider_data["npi"],
                defaults=provider_data,
            )
            order, _created = Order.objects.update_or_create(
                id=order_data["id"],
                defaults={
                    **order_data,
                    "patient": patient,
                    "provider": provider,
                },
            )
            CarePlan.objects.update_or_create(
                id=care_plan_data["id"],
                defaults={
                    **care_plan_data,
                    "order": order,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {len(MOCK_CARE_PLANS)} patients, providers, orders, and care plans."
            )
        )
