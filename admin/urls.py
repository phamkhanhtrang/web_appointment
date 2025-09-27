from django.urls import path

from admin import views
urlpatterns = [

path('', views.admin, name='admin'),
path('admin-login', views.admin_login, name='admin-login'),
path('admin-appointment', views.admin_appointment, name='admin-appointment'),
path('admin-doctor', views.admin_doctor, name='admin-doctor'),
path('admin-patient', views.admin_patient, name='admin-patient'),
path('admin-profile', views.admin_profile, name='admin-profile'),
path('admin-calendar/<str:doctor_username>/', views.admin_calendar, name='admin-calendar'),

]