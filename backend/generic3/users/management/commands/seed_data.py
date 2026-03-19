from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clinics.models import Clinic
from modules.models import Module, ClinicModule
from users.models import Staff, StaffClinic, Patient, PatientClinic, PatientDoctor
from medications.models import Medication, ClinicMedication

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with initial demo data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")

        # ── Clinics ────────────────────────────────────────────────────────────
        clinic1, _ = Clinic.objects.get_or_create(
            clinic_name="City Health Clinic",
            defaults={
                "clinic_url": "https://cityhealthclinic.example.com",
                "is_research_clinic": False,
            },
        )
        clinic2, _ = Clinic.objects.get_or_create(
            clinic_name="Research Medical Center",
            defaults={
                "clinic_url": "https://researchmedical.example.com",
                "is_research_clinic": True,
            },
        )

        # ── Modules ────────────────────────────────────────────────────────────
        mod_meds, _ = Module.objects.get_or_create(
            module_name="Medications",
            defaults={
                "module_description": "Track patient medications and prescriptions"
            },
        )
        mod_activities, _ = Module.objects.get_or_create(
            module_name="Activities",
            defaults={"module_description": "Track patient activities and exercises"},
        )
        mod_questionnaires, _ = Module.objects.get_or_create(
            module_name="Questionnaires",
            defaults={"module_description": "Patient questionnaires and surveys"},
        )

        for clinic in [clinic1, clinic2]:
            for module in [mod_meds, mod_activities, mod_questionnaires]:
                ClinicModule.objects.get_or_create(clinic=clinic, module=module)

        # ── Medications ────────────────────────────────────────────────────────
        medications_data = [
            ("Amoxicillin",      "CAP", "MG"),
            ("Ibuprofen",        "TAB", "MG"),
            ("Paracetamol",      "TAB", "MG"),
            ("Metformin",        "TAB", "MG"),
            ("Atorvastatin",     "TAB", "MG"),
            ("Lisinopril",       "TAB", "MG"),
            ("Omeprazole",       "CAP", "MG"),
            ("Salbutamol",       "INH", "MCG"),
            ("Insulin Glargine", "INJ", "UNIT"),
            ("Amoxicillin",      "SYR", "MG/ML"),
            ("Azithromycin",     "TAB", "MG"),
            ("Ciprofloxacin",    "TAB", "MG"),
            ("Dexamethasone",    "INJ", "MG"),
            ("Furosemide",       "TAB", "MG"),
            ("Amlodipine",       "TAB", "MG"),
            ("Losartan",         "TAB", "MG"),
            ("Sertraline",       "TAB", "MG"),
            ("Diazepam",         "TAB", "MG"),
            ("Morphine",         "INJ", "MG"),
            ("Ondansetron",      "TAB", "MG"),
        ]
        meds = []
        for med_name, med_form, med_unit in medications_data:
            med, _ = Medication.objects.get_or_create(
                med_name=med_name,
                med_form=med_form,
                defaults={"med_unit": med_unit},
            )
            meds.append(med)
        self.stdout.write(self.style.SUCCESS(f"  Seeded {len(meds)} medications"))

        # Assign all medications to both clinics
        for clinic in [clinic1, clinic2]:
            for med in meds:
                ClinicMedication.objects.get_or_create(clinic=clinic, medication=med)
        self.stdout.write(self.style.SUCCESS("  Linked medications to both clinics"))

        # ── Admin user ─────────────────────────────────────────────────────────
        if not User.objects.filter(email="admin@generic3.com").exists():
            User.objects.create_superuser(
                email="admin@generic3.com",
                password="Admin1234!",
                first_name="System",
                last_name="Admin",
            )
            self.stdout.write(
                self.style.SUCCESS("  Created admin: admin@generic3.com / Admin1234!")
            )

        # ── Clinic Managers ────────────────────────────────────────────────────
        managers = [
            (
                "manager@cityhealthclinic.com",
                "Manager1234!",
                "Alice",
                "Morgan",
                clinic1,
            ),
            (
                "manager2@cityhealthclinic.com",
                "Manager1234!",
                "Brian",
                "Wallace",
                clinic1,
            ),
            (
                "manager3@cityhealthclinic.com",
                "Manager1234!",
                "Carol",
                "Bennett",
                clinic1,
            ),
            (
                "manager@researchmedical.com",
                "Manager1234!",
                "David",
                "Fletcher",
                clinic2,
            ),
        ]
        for email, password, first, last, clinic in managers:
            if not User.objects.filter(email=email).exists():
                mgr_user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first,
                    last_name=last,
                    role="CLINIC_MANAGER",
                )
                mgr_staff = Staff.objects.create(
                    user=mgr_user, staff_type="CLINIC_MANAGER"
                )
                StaffClinic.objects.create(staff=mgr_staff, clinic=clinic)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created clinic manager: {email} / {password}"
                    )
                )

        # ── Doctors ────────────────────────────────────────────────────────────
        doctors = [
            ("doctor@cityhealthclinic.com", "Doctor1234!", "Bob", "Harris", clinic1),
            ("doctor2@cityhealthclinic.com", "Doctor1234!", "Elena", "Torres", clinic1),
            ("doctor3@cityhealthclinic.com", "Doctor1234!", "Frank", "Nguyen", clinic1),
            ("doctor@researchmedical.com", "Doctor1234!", "Grace", "Patel", clinic2),
        ]
        doc_staffs = {}
        for email, password, first, last, clinic in doctors:
            if not User.objects.filter(email=email).exists():
                doc_user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first,
                    last_name=last,
                    role="DOCTOR",
                )
                doc_staff = Staff.objects.create(user=doc_user, staff_type="DOCTOR")
                StaffClinic.objects.create(staff=doc_staff, clinic=clinic)
                self.stdout.write(
                    self.style.SUCCESS(f"  Created doctor: {email} / {password}")
                )
            else:
                doc_user = User.objects.get(email=email)
                doc_staff = doc_user.staff
            doc_staffs[email] = (doc_staff, clinic)

        primary_doc_staff, _ = doc_staffs["doctor@cityhealthclinic.com"]
        research_doc_staff, _ = doc_staffs["doctor@researchmedical.com"]

        # ── Patients ───────────────────────────────────────────────────────────
        patients = [
            (
                "patient@example.com",
                "Patient1234!",
                "Charlie",
                "Adams",
                clinic1,
                primary_doc_staff,
            ),
            (
                "patient2@example.com",
                "Patient1234!",
                "Hannah",
                "Collins",
                clinic1,
                primary_doc_staff,
            ),
            (
                "patient3@example.com",
                "Patient1234!",
                "Ivan",
                "Reed",
                clinic1,
                primary_doc_staff,
            ),
            (
                "patient4@example.com",
                "Patient1234!",
                "Julia",
                "Brooks",
                clinic1,
                primary_doc_staff,
            ),
        ]
        for email, password, first, last, clinic, doc_staff in patients:
            if not User.objects.filter(email=email).exists():
                pat_user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first,
                    last_name=last,
                    role="PATIENT",
                )
                patient = Patient.objects.create(user=pat_user)
                PatientClinic.objects.create(patient=patient, clinic=clinic)
                PatientDoctor.objects.create(
                    patient=patient, doctor=doc_staff, clinic=clinic
                )
                self.stdout.write(
                    self.style.SUCCESS(f"  Created patient: {email} / {password}")
                )

        # ── Research Patients ──────────────────────────────────────────────────
        research_patients = [
            (
                "research@example.com",
                "Research1234!",
                "Diana",
                "Cooper",
                clinic2,
                research_doc_staff,
            ),
            (
                "research2@example.com",
                "Research1234!",
                "Kevin",
                "Sanders",
                clinic2,
                research_doc_staff,
            ),
            (
                "research3@example.com",
                "Research1234!",
                "Laura",
                "Jenkins",
                clinic2,
                research_doc_staff,
            ),
            (
                "research4@example.com",
                "Research1234!",
                "Marcus",
                "Powell",
                clinic2,
                research_doc_staff,
            ),
        ]
        for email, password, first, last, clinic, doc_staff in research_patients:
            if not User.objects.filter(email=email).exists():
                res_user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first,
                    last_name=last,
                    role="RESEARCH_PATIENT",
                )
                res_patient = Patient.objects.create(user=res_user)
                PatientClinic.objects.create(patient=res_patient, clinic=clinic)
                PatientDoctor.objects.create(
                    patient=res_patient, doctor=doc_staff, clinic=clinic
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created research patient: {email} / {password}"
                    )
                )

        self.stdout.write(self.style.SUCCESS("\nSeed data complete."))
        self.stdout.write("\nCredentials summary:")
        self.stdout.write("  Admin:             admin@generic3.com / Admin1234!")
        self.stdout.write(
            "  Managers (x4):     manager@cityhealthclinic.com  ... / Manager1234!"
        )
        self.stdout.write(
            "  Doctors  (x4):     doctor@cityhealthclinic.com   ... / Doctor1234!"
        )
        self.stdout.write(
            "  Patients (x4):     patient@example.com           ... / Patient1234!"
        )
        self.stdout.write(
            "  Research (x4):     research@example.com          ... / Research1234!"
        )
