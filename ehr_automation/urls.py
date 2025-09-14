# urls.py
from django.contrib import admin
from django.urls import path, include
from ehr_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.HomePageView.as_view(), name='home'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('complete-registration/', views.complete_registration, name='complete_registration'),
    path('schedule-appointment/', views.schedule_appointment, name='schedule_appointment'),
    path('request-refill/', views.request_refill, name='request_refill'),
    path('record-vitals/', views.record_vitals, name='record_vitals'),
    path('add-diagnosis/', views.add_diagnosis, name='add_diagnosis'),
    path('prescribe-medication/', views.prescribe_medication, name='prescribe_medication'),
    path('add-consultation-note/', views.add_consultation_note, name='add_consultation_note'),
    path('generate-report/', views.generate_report, name='generate_report'),  # Add this line
    
    # Add password reset URLs
    path('password_reset/', include('django.contrib.auth.urls')),
]

# Error handlers
handler400 = 'ehr_app.views.bad_request'
handler403 = 'ehr_app.views.permission_denied'
handler404 = 'ehr_app.views.page_not_found'
handler500 = 'ehr_app.views.server_error'