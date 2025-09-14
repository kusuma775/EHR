from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Doctor, Patient
from django.contrib.auth.models import Group


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_doctor:
            Doctor.objects.create(user=instance)
            doctor_group = Group.objects.get_or_create(name='Doctor')[0]
            instance.groups.add(doctor_group)
        else:
            Patient.objects.create(user=instance)
            patient_group = Group.objects.get_or_create(name='Patient')[0]
            instance.groups.add(patient_group)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'doctor'):
        instance.doctor.save()
    elif hasattr(instance, 'patient'):
        instance.patient.save()