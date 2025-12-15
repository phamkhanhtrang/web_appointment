import json
from django.contrib import messages

from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from userauths.models import Appointment, Prescription,PrescriptionDetail
from userauths.models import Doctor,User, Patient
from django.db.models import Count,Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect
from django.utils.timezone import now
from userauths.decorators import role_required
from userauths.models import format_vnd
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Prefetch



# Create your views here.
@role_required('doctor')
def doctor_view(request):
    try:
        doctor = request.user.doctor_profile

        # Lấy toàn bộ appointment của bác sĩ (từ 2 DB nếu có)
        appointments = list(
            Appointment.objects.using('specialty1')
            .filter(doctor_id=doctor.id)
        ) + list(
            Appointment.objects.using('specialty2')
            .filter(doctor_id=doctor.id)
        )

        # Tổng số cuộc hẹn
        total_appointments = len(appointments)

        # Tổng số bệnh nhân (distinct patient_id)
        total_patients = len(set(a.patient_id for a in appointments))

        # Tổng doanh thu
        total_revenue = sum(
            a.price for a in appointments
            if a.status == 'completed' and a.price
        )
        total_revenue_vnd = format_vnd(total_revenue)

        # ---------- THỐNG KÊ THEO BỆNH NHÂN ----------
        patient_counter = {}
        for a in appointments:
            patient_counter[a.patient_id] = patient_counter.get(a.patient_id, 0) + 1

        patients = Patient.objects.filter(id__in=patient_counter.keys()) \
            .select_related('user')

        patient_stats = [
            {
                'username': p.user.username,
                'total': patient_counter.get(p.id, 0)
            }
            for p in patients
        ]

        patient_stats.sort(key=lambda x: x['total'], reverse=True)

        # ---------- BIỂU ĐỒ THEO THÁNG ----------
        monthly_map = {}
        for a in appointments:
            if a.status != 'completed':
                continue
            month = a.appointment_time.strftime('%Y-%m')
            monthly_map.setdefault(month, {'appointments': 0, 'revenue': 0})
            monthly_map[month]['appointments'] += 1
            monthly_map[month]['revenue'] += float(a.price or 0)

        chart_data = [
            {
                'month': month,
                'appointments': data['appointments'],
                'revenue': data['revenue']
            }
            for month, data in sorted(monthly_map.items())
        ]

    except Doctor.DoesNotExist:
        appointments = []
        patient_stats = []
        total_patients = 0
        total_appointments = 0
        total_revenue_vnd = 0
        chart_data = []

    context = {
        'appointments': appointments,
        'patient_stats': patient_stats,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'total_revenue_vnd': total_revenue_vnd,
        'chart_data': json.dumps(chart_data),
    }

    return render(request, 'doctor/index.html', context)

@role_required('doctor')
    
def appointment_view(request):
    try:
        doctor = request.user.doctor_profile

        # ===== Map khoa =====
        SPECIALTY_MAP = {
            1: "Khoa Nội",
            2: "Khoa Ngoại",
        }
        filter_specialty = request.GET.get("specialty")  # "1" hoặc "2"

        appointments = []

        if not filter_specialty or filter_specialty == "1":
            for a in Appointment.objects.using('specialty1').filter(doctor_id=doctor.id):
                a.specialty_label = SPECIALTY_MAP.get(a.specialty_id, "Không xác định")
                a._db = 'specialty1'
                appointments.append(a)
        if not filter_specialty or filter_specialty == "2":
            for a in Appointment.objects.using('specialty2').filter(doctor_id=doctor.id):
                a.specialty_label = SPECIALTY_MAP.get(a.specialty_id, "Không xác định")
                a._db = 'specialty2'
                appointments.append(a)
        for a in appointments:
            if a.appointment_time < now() and a.status not in ['completed', 'cancelled']:
                a.status = 'cancelled'
                a.save(using=a._db)

        appointments.sort(key=lambda x: x.appointment_time, reverse=True)

        patient_ids = {a.patient_id for a in appointments}
        patient_map = {
            p.id: p
            for p in Patient.objects.filter(id__in=patient_ids)
            .select_related('user')
        }

        for a in appointments:
            a.patient_obj = patient_map.get(a.patient_id)
        if request.method == 'POST':
            appointment_id = int(request.POST.get('appointment_id'))
            new_status = request.POST.get('status')

            for a in appointments:
                if a.id == appointment_id:
                    a.status = new_status
                    a.save(using=a._db)
                    break

    except Doctor.DoesNotExist:
        appointments = []

    context = {
        'appointments': appointments,
        'current_specialty': filter_specialty
    }
    return render(request, 'doctor/appointment-list.html', context)

@role_required('doctor')
def patient_view(request):
    try:
        doctor = request.user.doctor_profile
        appointments = []

        # ===== LẤY LỊCH HẸN TỪ CÁC DB =====
        for db in ['specialty1', 'specialty2']:
            qs = Appointment.objects.using(db).filter(doctor_id=doctor.id)
            for a in qs:
                appointments.append(a)

        # ===== GROUP THEO PATIENT_ID =====
        patient_stats = {}
        for a in appointments:
            pid = a.patient_id
            if pid not in patient_stats:
                patient_stats[pid] = {
                    'total': 0,
                    'total_price': 0
                }
            patient_stats[pid]['total'] += 1
            patient_stats[pid]['total_price'] += a.price or 0

        # ===== JOIN PATIENT =====
        patients = Patient.objects.filter(
            id__in=patient_stats.keys()
        ).select_related('user')

        result = []
        for p in patients:
            stat = patient_stats.get(p.id)
            result.append({
                'full_name': p.user.get_full_name(),
                'phone_number': p.user.phone_number,
                'total': stat['total'],
                'total_price_vnd': format_vnd(stat['total_price']),
            })

        result.sort(key=lambda x: x['total'], reverse=True)

    except Doctor.DoesNotExist:
        result = []

    context = {
        'patient_stats': result
    }
    return render(request, 'doctor/patient-list.html', context)
@role_required('doctor')
def profile_view(request):
    user =request.user    
    if request.method == 'POST':
        username = request.POST.get('username')
        full_name = request.POST.get('fullname')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')
        avatar = request.FILES.get('avatar')

        if username and username != user.username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                messages.error(request, "Tên đăng nhập đã được sử dụng, vui lòng chọn tên khác.")
                return redirect('doctor_profile')
            user.username = username

        if full_name:
            parts = full_name.strip().split()
            if len(parts) == 1:
                user.first_name = parts[0]
                user.last_name = ''
            else:
                user.first_name = ' '.join(parts[:-1])
                user.last_name = parts[-1]

        if phone:
            user.phone_number = phone

        if email and email != user.email:
            if User.objects.filter(email=email).exclude(pk=user.pk).exists():
                messages.error(request, "Email đã tồn tại, vui lòng dùng email khác.")
                return redirect('doctor_profile')
            user.email = email

        if password:
            user.set_password(password)  # luôn hash
        if avatar:
            user.avatar = avatar
            
        try:
            user.save()
            messages.success(request, "Cập nhật thông tin thành công!")
        except IntegrityError:
            messages.error(request, "Có lỗi xảy ra, vui lòng thử lại.")
         
        return redirect('doctor_profile')
    template = loader.get_template('doctor/profile.html')
    return HttpResponse(template.render({}, request))

def prescription(request):
    template = loader.get_template('doctor/prescription.html')
    return HttpResponse(template.render({}, request))

def calendar_view(request):
    doctor = request.user.doctor_profile

    events = []
    appointments = []

    # ===== LẤY LỊCH HẸN TỪ CÁC DB =====
    for db in ['specialty1', 'specialty2']:
        qs = Appointment.objects.using(db).filter(
            doctor_id=doctor.id,
            status__in=['confirmed', 'completed', 'pending']
        )
        for a in qs:
            a._db = db
            appointments.append(a)

    # ===== JOIN PATIENT (APP LAYER) =====
    patient_ids = {a.patient_id for a in appointments}
    patient_map = {
        p.id: p
        for p in Patient.objects.filter(id__in=patient_ids).select_related('user')
    }

    # ===== TẠO EVENT CHO FULLCALENDAR =====
    for a in appointments:
        patient = patient_map.get(a.patient_id)

        events.append({
            'id': a.id,
            'title': patient.user.get_full_name() if patient else 'Không rõ bệnh nhân',
            'start': a.appointment_time.replace(tzinfo=None).isoformat(),
            'status': a.status,
            'patient_name': patient.user.get_full_name() if patient else '',
        })

    # ===== KÊ ĐƠN =====
    # ===== KÊ ĐƠN =====
    if request.method == 'POST':
        appointment_id = int(request.POST.get('appointment_id'))
        diagnosis = request.POST.get('diagnosis')
        note = request.POST.get('note')
        appointment = None
        for a in appointments:
            if a.id == appointment_id:
                appointment = a
                break
        if not appointment:
            messages.error(request, "Không tìm thấy lịch hẹn.")
            return redirect('calendar_view')

    # 🔥 LẤY DB ĐÚNG CỦA APPOINTMENT
        db_name = appointment._db

    # ✅ CREATE PRESCRIPTION ĐÚNG DB + ĐÚNG FK
        prescription = Prescription.objects.using(db_name).create(
        appointment=appointment,   # ✅ dùng object
        doctor_id=doctor.id,
        patient_id=appointment.patient_id,
        diagnosis=diagnosis,
        note=note
    )

        medicine_names = request.POST.getlist('medicine_name[]')
        dosages = request.POST.getlist('dosage[]')
        usages = request.POST.getlist('usage[]')
        quantities = request.POST.getlist('quantity[]')

        for i in range(len(medicine_names)):
            if medicine_names[i].strip():
                PrescriptionDetail.objects.using(db_name).create(
                    prescription=prescription,
                medication_name=medicine_names[i],
                dosage=dosages[i],
                usage=usages[i],
                quantity=int(quantities[i]) if quantities[i].isdigit() else 1
            )

        messages.success(request, "Kê đơn thành công.")
        return redirect('calendar_view')


    return render(
        request,
        'doctor/calendar.html',
        {'events_json': json.dumps(events)}
    )