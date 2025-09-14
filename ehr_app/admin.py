from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Doctor, Patient

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_doctor', 'is_patient')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('is_doctor', 'is_patient')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Doctor)
admin.site.register(Patient)
