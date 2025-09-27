from django.contrib.auth.models import AbstractUser
from django.db import models

# Base User Model
class User(AbstractUser):
    ROLE_CHOICES = (
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        return f"{self.username} ({self.role})"

# Doctor info
class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"

    def price_vnd(self):
        return f"{int(self.price):,}".replace(',', '.') + " VND"
    

class DoctorSchedule(models.Model):
    STATUS_CHOICES = (
        ('work', 'Làm việc'), 
        ('off', 'Nghỉ'),
        )
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='work')

    class Meta:
        unique_together = ('doctor', 'date')  # Đảm bảo mỗi bác sĩ có một lịch duy nhất cho mỗi ngày
        ordering = ['date']

    def __str__(self):
        return f"{self.doctor} - {self.date} ({self.get_status_display()})"


# Patient info
class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return self.user.get_full_name()

# Appointment
class Appointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    appointment_time = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    STATUS_CHOICES=[
        ('pending', 'Chờ xác nhận'),
        ('confirmed', 'Đã xác nhận'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã hủy'),
    ]
    status = models.CharField(max_length=20, choices = STATUS_CHOICES, default='pending')

    PAYMENT_CHOICES = [
        ('cash', 'Tiền mặt'),
        ('card', 'Thẻ'),
        ('momo', 'Momo'),
        ('insurance', 'Bảo hiểm')
    ]
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    
    def price_vnd(self):
        return f"{int(self.price):,}".replace(',', '.') + " VND"
    def __str__(self):
        return f"{self.patient.user.username} hẹn với {self.doctor.user.username} lúc {self.appointment_time.strftime('%Y-%m-%d %H:%M')}"

class Prescription(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='prescription')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    diagnosis = models.CharField(max_length=255, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription for {self.patient.user.username} on {self.created_at.strftime('%Y-%m-%d')}"
    
class PrescriptionDetail(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='details')
    medication_name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100, blank=True, null=True)
    usage = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.PositiveBigIntegerField(default=1)

    def __str__(self):
        return f"{self.medication_name} - {self.dosage}"

def format_vnd(amount):
    if amount is None:
        return "0 VND"
    return f"{int(amount):,}".replace(',', '.') + " VND"
