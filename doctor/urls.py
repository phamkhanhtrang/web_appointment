from django.urls import path

from doctor import views
urlpatterns = [

path('', views.doctor_view, name='doctor'),
path('appoitment-list/', views.appointment_view, name='appoitment-list'),
path('patient-list/', views.patient_view, name="patient-list"),
path('profile/', views.profile_view, name="doctor_profile"),
path('prescription/', views.prescription, name= "prescription"),
path('calendar/', views.calendar_view, name='calendar_view'),

]