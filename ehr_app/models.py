from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from datetime import date

class User(AbstractUser):
    is_doctor = models.BooleanField(default=False)
    is_patient = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor')
    specialty = models.CharField(max_length=100, blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient')
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='patients')
    dob = models.DateField(null=True, blank=True)
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in cm
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in kg
    allergies = models.TextField(blank=True)
    medical_history = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    surgeries = models.TextField(blank=True)
    family_medical_history = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    otc_medications = models.TextField(blank=True)
    supplements = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    registration_complete = models.BooleanField(default=False)
    last_visit = models.DateField(null=True, blank=True)
    
    @property
    def age(self):
        if self.dob:
            today = date.today()
            return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return None
    
    def __str__(self):
        return self.user.get_full_name()

class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    date = models.DateField()
    time = models.TimeField()
    reason = models.TextField()
    
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('No Show', 'No Show'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.date} at {self.time}"

class Prescription(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescriptions')
    medication = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=50, blank=True)
    instructions = models.TextField(blank=True)
    refills_left = models.PositiveIntegerField(default=0)
    date_prescribed = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.medication} for {self.patient}"

class TestResult(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='test_results')
    ordered_by = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='ordered_tests')
    test_name = models.CharField(max_length=100)
    test_date = models.DateField()
    result_summary = models.TextField()
    report_file = models.FileField(upload_to='test_reports/', blank=True, null=True)
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Abnormal', 'Abnormal'),
        ('Critical', 'Critical'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    def __str__(self):
        return f"{self.test_name} for {self.patient}"

class ConsultationNote(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultation_notes')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='consultation_notes')
    date = models.DateField()
    reason = models.TextField()
    diagnosis = models.TextField()
    treatment = models.TextField()
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Consultation for {self.patient} on {self.date}"

class BillingRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='billing_records')
    invoice_number = models.CharField(max_length=50, unique=True)
    date_issued = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    service_description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue'),
        ('Cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    def __str__(self):
        return f"Invoice #{self.invoice_number} for {self.patient}"

class Payment(models.Model):
    billing_record = models.ForeignKey(BillingRecord, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Insurance', 'Insurance'),
        ('Bank Transfer', 'Bank Transfer'),
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    receipt = models.FileField(upload_to='payment_receipts/', blank=True, null=True)
    
    def __str__(self):
        return f"Payment of ${self.amount} for {self.billing_record}"

class VitalsRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vitals_records')
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recorded_vitals')
    date = models.DateField()
    blood_pressure_systolic = models.PositiveIntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.PositiveIntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)  # in Fahrenheit
    pulse = models.PositiveIntegerField(null=True, blank=True)  # bpm
    oxygen_saturation = models.PositiveIntegerField(null=True, blank=True)  # %
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in kg
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # in cm
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Vitals for {self.patient} on {self.date}"


