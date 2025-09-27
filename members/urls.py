from django.urls import path, include
from . import views

# app_name = 'members'
urlpatterns = [
    path('', views.members, name='members'),       # /members/
    path('about/', views.about, name='about'),
    path('service/', views.service, name='service'),
    path('appointment/<str:doctor_username>/', views.book_appointment_view, name='appointment'),
    path('profile/', views.profile, name='profile'),
    path('paypal/', include('paypal.standard.ipn.urls')),   # PayPal IPN URLs
    
    path('payment-complete/<str:appointment_id>/', views.payment_complete_view, name='payment-complete'),
    path('payment-failed/', views.payment_failed_view, name='payment-failed'),
]