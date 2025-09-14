from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('complete-registration/', views.complete_registration, name='complete_registration'),
]