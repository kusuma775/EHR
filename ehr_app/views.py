from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Patient, Doctor, User, Appointment, Prescription, TestResult, ConsultationNote, BillingRecord, Payment, VitalsRecord
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from datetime import date
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO

class HomePageView(TemplateView):
    template_name = "ehr_app/home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['features'] = [
            "Secure patient records",
            "Easy access to medical data",
            "Appointment scheduling",
            "e-Prescribing",
            "Analytics dashboard",
            "Mobile access"
        ]
        return context

class RegisterView(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'registration/login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'registration/login.html')

@login_required
def dashboard(request):
    context = {}
    
    if request.user.is_superuser:
        context['is_admin'] = True
    elif hasattr(request.user, 'doctor'):
        doctor = request.user.doctor
        patients = Patient.objects.filter(doctor=doctor)
        today = date.today()
        
        # Doctor-specific data
        context.update({
            'is_doctor': True,
            'doctor_patients': patients,
            'today_appointments': Appointment.objects.filter(doctor=doctor, date=today).count(),
            'pending_prescriptions': Prescription.objects.filter(doctor=doctor, is_active=True).count(),
            'pending_test_results': TestResult.objects.filter(ordered_by=doctor, status='Pending').count(),
            'todays_appointments': Appointment.objects.filter(doctor=doctor, date=today).order_by('time'),
            'upcoming_appointments': Appointment.objects.filter(doctor=doctor, date__gt=today).order_by('date', 'time')[:5],
            'completed_test_results': TestResult.objects.filter(ordered_by=doctor, status='Completed').order_by('-test_date')[:5],
        })
    elif hasattr(request.user, 'patient'):
        patient = request.user.patient
        today = date.today()
        
        # Patient-specific data
        context.update({
            'is_patient': True,
            'patient': patient,
            'appointments': Appointment.objects.filter(patient=patient, date__gte=today).order_by('date', 'time'),
            'prescriptions': Prescription.objects.filter(patient=patient, is_active=True),
            'test_results': TestResult.objects.filter(patient=patient).order_by('-test_date'),
            'outstanding_bills': BillingRecord.objects.filter(patient=patient, status='Pending'),
            'payment_history': Payment.objects.filter(billing_record__patient=patient).order_by('-payment_date'),
            'consultation_notes': ConsultationNote.objects.filter(patient=patient).order_by('-date'),
            'doctors': Doctor.objects.all(),  # For appointment scheduling
        })
    
    return render(request, 'ehr_app/dashboard.html', context)

@login_required
@require_POST
def complete_registration(request):
    try:
        patient = request.user.patient
        patient.dob = request.POST.get('dob')
        patient.gender = request.POST.get('gender')
        patient.blood_type = request.POST.get('blood_type')
        patient.allergies = request.POST.get('allergies')
        patient.medical_history = request.POST.get('medical_history')
        patient.visit_reason = request.POST.get('visit_reason')
        patient.registration_complete = True
        patient.save()
        messages.success(request, 'Registration completed successfully!')
    except Exception as e:
        messages.error(request, f'Error completing registration: {str(e)}')
    return redirect('dashboard')

@login_required
@require_POST
def schedule_appointment(request):
    try:
        patient = request.user.patient
        doctor = Doctor.objects.get(id=request.POST.get('doctor'))
        appointment_date = request.POST.get('date')
        appointment_time = request.POST.get('time')
        reason = request.POST.get('reason')
        
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=appointment_date,
            time=appointment_time,
            reason=reason
        )
        
        messages.success(request, 'Appointment scheduled successfully!')
    except Exception as e:
        messages.error(request, f'Error scheduling appointment: {str(e)}')
    return redirect('dashboard')

@login_required
@require_POST
def request_refill(request):
    try:
        prescription_id = request.POST.get('prescription')
        notes = request.POST.get('notes', '')
        
        # In a real application, this would send a notification to the doctor
        messages.success(request, 'Refill request submitted. Your doctor will review it shortly.')
    except Exception as e:
        messages.error(request, f'Error requesting refill: {str(e)}')
    return redirect('dashboard')

@login_required
@require_POST
def record_vitals(request):
    try:
        patient = request.user.patient
        blood_pressure = request.POST.get('blood_pressure')
        temperature = request.POST.get('temperature')
        pulse = request.POST.get('pulse')
        oxygen = request.POST.get('oxygen')
        weight = request.POST.get('weight')
        notes = request.POST.get('notes', '')
        
        # Parse blood pressure if provided
        bp_systolic, bp_diastolic = None, None
        if blood_pressure and '/' in blood_pressure:
            bp_parts = blood_pressure.split('/')
            if len(bp_parts) == 2:
                bp_systolic = int(bp_parts[0]) if bp_parts[0].isdigit() else None
                bp_diastolic = int(bp_parts[1]) if bp_parts[1].isdigit() else None
        
        VitalsRecord.objects.create(
            patient=patient,
            recorded_by=request.user,
            date=date.today(),
            blood_pressure_systolic=bp_systolic,
            blood_pressure_diastolic=bp_diastolic,
            temperature=float(temperature) if temperature else None,
            pulse=int(pulse) if pulse else None,
            oxygen_saturation=int(oxygen) if oxygen else None,
            weight=float(weight) if weight else None,
            notes=notes
        )
        
        messages.success(request, 'Vitals recorded successfully!')
    except Exception as e:
        messages.error(request, f'Error recording vitals: {str(e)}')
    return redirect('dashboard')

@login_required
@require_POST
def add_diagnosis(request):
    try:
        if not hasattr(request.user, 'doctor'):
            raise Exception('Only doctors can add diagnoses')
            
        patient = Patient.objects.get(id=request.POST.get('patient'))
        diagnosis_date = request.POST.get('date')
        code = request.POST.get('code', '')
        description = request.POST.get('description')
        notes = request.POST.get('notes', '')
        
        # In a real application, this would create a Diagnosis record
        messages.success(request, 'Diagnosis added successfully!')
    except Exception as e:
        messages.error(request, f'Error adding diagnosis: {str(e)}')
    return redirect('dashboard')

@login_required
@require_POST
def prescribe_medication(request):
    try:
        if not hasattr(request.user, 'doctor'):
            raise Exception('Only doctors can prescribe medications')
            
        patient = Patient.objects.get(id=request.POST.get('patient'))
        medication = request.POST.get('medication')
        dosage = request.POST.get('dosage')
        frequency = request.POST.get('frequency')
        duration = request.POST.get('duration', '')
        refills = int(request.POST.get('refills', 0))
        instructions = request.POST.get('instructions', '')
        
        Prescription.objects.create(
            patient=patient,
            doctor=request.user.doctor,
            medication=medication,
            dosage=dosage,
            frequency=frequency,
            duration=duration,
            refills_left=refills,
            instructions=instructions
        )
        
        messages.success(request, 'Prescription created successfully!')
    except Exception as e:
        messages.error(request, f'Error prescribing medication: {str(e)}')
    return redirect('dashboard')

@login_required
@require_POST
def add_consultation_note(request):
    try:
        if not hasattr(request.user, 'doctor'):
            raise Exception('Only doctors can add consultation notes')
            
        patient = Patient.objects.get(id=request.POST.get('patient'))
        consultation_date = request.POST.get('date')
        reason = request.POST.get('reason')
        diagnosis = request.POST.get('diagnosis')
        treatment = request.POST.get('treatment')
        notes = request.POST.get('notes', '')
        
        ConsultationNote.objects.create(
            patient=patient,
            doctor=request.user.doctor,
            date=consultation_date,
            reason=reason,
            diagnosis=diagnosis,
            treatment=treatment,
            notes=notes
        )
        
        messages.success(request, 'Consultation notes added successfully!')
    except Exception as e:
        messages.error(request, f'Error adding consultation notes: {str(e)}')
    return redirect('dashboard')

@login_required
def generate_report(request):
    if not hasattr(request.user, 'doctor'):
        messages.error(request, 'Only doctors can generate reports')
        return redirect('dashboard')
    
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        patient_id = request.POST.get('patient')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        format = request.POST.get('format', 'pdf')
        
        try:
            patient = Patient.objects.get(id=patient_id) if patient_id else None
            
            if report_type == 'patientSummary':
                context = {
                    'patient': patient,
                    'appointments': Appointment.objects.filter(patient=patient).order_by('-date'),
                    'prescriptions': Prescription.objects.filter(patient=patient),
                    'test_results': TestResult.objects.filter(patient=patient),
                    'consultation_notes': ConsultationNote.objects.filter(patient=patient),
                }
                
                if format == 'pdf':
                    html_string = render_to_string('reports/patient_summary.html', context)
                    result = BytesIO()
                    
                    pdf = pisa.pisaDocument(
                        BytesIO(html_string.encode("UTF-8")),
                        result,
                        encoding='UTF-8'
                    )
                    
                    if not pdf.err:
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = f'attachment; filename="patient_summary_{patient.user.username}.pdf"'
                        response.write(result.getvalue())
                        return response
                    else:
                        messages.error(request, 'Error generating PDF')
                        return redirect('dashboard')
                
                # Rest of your format handling remains the same...
                
        except Exception as e:
            messages.error(request, f'Error generating report: {str(e)}')
            return redirect('dashboard')
    
    messages.error(request, 'Invalid report request')
    return redirect('dashboard')
@login_required
def get_patient_details(request, patient_id):
    if not hasattr(request.user, 'doctor'):
        return JsonResponse({'error': 'Only doctors can view patient details'}, status=403)
    
    try:
        patient = Patient.objects.get(id=patient_id)
        return JsonResponse({
            'name': patient.user.get_full_name(),
            'dob': patient.dob.strftime('%Y-%m-%d') if patient.dob else 'Not specified',
            'gender': patient.get_gender_display(),
            'blood_type': patient.blood_type or 'Not specified',
            'allergies': patient.allergies or 'None reported',
            'conditions': patient.chronic_conditions or 'None reported',
            'medications': patient.current_medications or 'None',
            'last_appointment': patient.last_appointment.strftime('%Y-%m-%d') if patient.last_appointment else 'No visits'
        })
    except Patient.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def logout_view(request):
    logout(request)
    return redirect('home')

def bad_request(request, exception):
    return render(request, 'errors/400.html', status=400)

def permission_denied(request, exception):
    return render(request, 'errors/403.html', status=403)

def page_not_found(request, exception):
    return render(request, 'errors/404.html', status=404)

def server_error(request):
    return render(request, 'errors/500.html', status=500)