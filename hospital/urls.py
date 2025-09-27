"""
URL configuration for hospital project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.contrib import admin
from django.urls import include, path
from members import views
from userauths import views as userauth_views
from doctor import views as doctor_views
from django.conf import settings
from django.conf.urls.static import static
from admin import views as admin_views



urlpatterns = [
    path('', include('members.urls')),
    # path('admin/', admin.site.urls),
    path('about/', views.about, name='about'),
    path('service/', views.service, name='service'),
    
    path('register/', userauth_views.register_view, name='register'),
    path('login/', userauth_views.login_view, name='login'),
    path('logout/', userauth_views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('user/', include('userauths.urls')),
    path('doctor/', include('doctor.urls')),    
path('doctor/appointment-list/', doctor_views.appointment_view, name='appoitment-list'),
path('doctor/patient-list/', doctor_views.patient_view, name="patient-list"),
path('doctor/profile/', doctor_views.profile_view, name="doctor_profile"), 
path('doctor/prescription', doctor_views.prescription, name="prescription"), 
    path('admin/', include('admin.urls')),
    path('admin/admin-login', admin_views.admin_login, name='admin-login'),
    path('admin/admin-appointment', admin_views.admin_appointment, name='admin-appointment'),
    path('admin/admin-doctor', admin_views.admin_doctor, name='admin-doctor'),
    path('admin/admin-patient', admin_views.admin_patient, name='admin-patient'),
    path('admin/admin-profile', admin_views.admin_profile, name='admin-profile'),
    path('admin/admin-calendar/<str:doctor_username>/', admin_views.admin_calendar, name='admin-calendar'),

    # path('calendar/export-excel/', admin_views.export_excel, name='export_excel'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)