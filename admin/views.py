from collections import defaultdict
import json
from django.utils.timezone import localtime
from django.template import loader
from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from userauths.models import Appointment,Patient, Doctor, DoctorSchedule
from django.db.models import Count, Sum, Max, Min,Q,Case,When,F,IntegerField,OuterRef, Subquery
from django.db.models.functions import TruncMonth, TruncDay
from django.http import JsonResponse
from django.utils.dateparse import parse_date
import pandas as pd
from userauths.models import format_vnd
from django.utils.timezone import now
from django.contrib import messages
from django.db import IntegrityError


# Create your views here.
def admin(request):
    try:
        admin_total_patients = Patient.objects.count()
        admin_total_doctors = Doctor.objects.count()
        admin_total_appointments = Appointment.objects.count()
        admin_total_revenue = Appointment.objects.filter(status = 'completed').aggregate(total=Sum('price'))['total'] or 0    
        admin_total_revenue_vnd = format_vnd(admin_total_revenue)

        appointments = Appointment.objects.all().order_by('-appointment_time')

        monthly_stats = Appointment.objects.filter(status = 'completed') \
            .annotate(month=TruncMonth('appointment_time')) \
            .values('month') \
            .annotate(admin_total_appointments=Count('id'), admin_total_revenue=Sum('price')) \
            .order_by('month')

        admin_chart_data = [
            {
                'month': stat['month'].strftime('%Y-%m'),
                'appointments': stat['admin_total_appointments'],
                'revenue': float(stat['admin_total_revenue']) if stat['admin_total_revenue'] else 0
            }
            for stat in monthly_stats
        ]

    except Exception as e:
        appointments = []
        admin_total_patients = 0
        admin_total_doctors = 0
        admin_total_appointments = 0
        admin_total_revenue_vnd = 0
        admin_chart_data = []

    context = {
        'admin_total_patients': admin_total_patients,
        'admin_total_doctors': admin_total_doctors,
        'admin_total_appointments': admin_total_appointments,
        'admin_total_revenue_vnd': admin_total_revenue_vnd,
        'appointments': appointments,
        'admin_chart_data': json.dumps(admin_chart_data),
    }
    return render(request, 'admin/index.html', context)

def admin_login(request):
    template = loader.get_template('admin/login.html')
    return HttpResponse(template.render({}, request))    

def admin_appointment(request):
    DB_LIST = ['specialty1', 'specialty2']

    # ===== HỦY LỊCH QUÁ HẠN =====
    for db in DB_LIST:
        Appointment.objects.using(db).filter(
            appointment_time__lt=now()
        ).exclude(
            status__in=['completed', 'cancelled']
        ).update(status='cancelled')

    # ===== LẤY TẤT CẢ APPOINTMENT =====
    all_appointments = []
    for db in DB_LIST:
        for a in Appointment.objects.using(db).all():
            a._db = db
            all_appointments.append(a)

    # ===== JOIN DOCTOR + PATIENT (DB CHUNG) =====
    doctor_ids = {a.doctor_id for a in all_appointments}
    patient_ids = {a.patient_id for a in all_appointments}

    doctor_map = {
        d.id: d
        for d in Doctor.objects.filter(id__in=doctor_ids)
        .select_related('user')
    }

    patient_map = {
        p.id: p
        for p in Patient.objects.filter(id__in=patient_ids)
        .select_related('user')
    }

    for a in all_appointments:
        a.doctor_obj = doctor_map.get(a.doctor_id)
        a.patient_obj = patient_map.get(a.patient_id)

    # ===== THỐNG KÊ TỔNG =====
    admin_total_appointments = len(all_appointments)

    admin_total_revenue = sum(
        float(a.price)
        for a in all_appointments
        if a.status == 'completed'
    )
    admin_total_revenue_vnd = format_vnd(admin_total_revenue)

    # ===== 10 LỊCH MỚI NHẤT =====
    admin_list_appointment = sorted(
        all_appointments,
        key=lambda x: x.appointment_time,
        reverse=True
    )[:10]

    # ===== THỐNG KÊ THEO NGÀY =====
    daily_map = defaultdict(lambda: {
        'appointments': 0,
        'revenue': 0,
        'confirmed': 0,
        'pending': 0,
        'completed': 0,
        'cancelled': 0,
    })

    for a in all_appointments:
        day = a.appointment_time.date().strftime('%Y-%m-%d')
        daily_map[day]['appointments'] += 1
        daily_map[day][a.status] += 1
        if a.status == 'completed':
            daily_map[day]['revenue'] += float(a.price)

    admin_chart_data = [
        {
            'day': day,
            **data
        }
        for day, data in sorted(daily_map.items())
    ]

    context = {
        'admin_total_appointments': admin_total_appointments,
        'admin_total_revenue_vnd': admin_total_revenue_vnd,
        'admin_list_appointment': admin_list_appointment,
        'admin_chart_data': json.dumps(admin_chart_data),
    }

    return render(request, 'admin/appointment-list.html', context)

def admin_doctor(request):
    from collections import defaultdict

    # ===== Doctor (default DB) =====
    admin_total_doctors = Doctor.objects.using('default').count()

    # ===== Appointment từ 2 DB =====
    all_appointments = []

    for db_name in ['specialty1', 'specialty2']:
        appointments = Appointment.objects.using(db_name).all()
        for a in appointments:
            a._state.db = db_name  # giữ DB info cho router
        all_appointments.extend(appointments)

    admin_total_appointments = len(all_appointments)

    # ===== Group theo doctor + day =====
    daily_map = defaultdict(int)
    for a in all_appointments:
        day = a.appointment_time.date()
        daily_map[(a.doctor_id, day)] += 1

    # ===== Doctor info =====
    doctor_ids = {a.doctor_id for a in all_appointments}
    doctors = Doctor.objects.using('default').filter(id__in=doctor_ids)
    doctor_map = {d.id: d for d in doctors}

    # ===== Chart data =====
    admin_chart_data = []
    for (doctor_id, day), total in daily_map.items():
        doctor = doctor_map.get(doctor_id)
        if not doctor:
            continue
        admin_chart_data.append({
            'day': day.strftime('%Y-%m-%d'),
            'appointments': total,
            'doctor': f"{doctor.user.first_name} {doctor.user.last_name}",
        })

    # ===== Doctor list + total appointment =====
    doctor_total_map = defaultdict(int)
    for a in all_appointments:
        doctor_total_map[a.doctor_id] += 1

    admin_list_doctor = Doctor.objects.using('default').all()
    for d in admin_list_doctor:
        d.total = doctor_total_map.get(d.id, 0)

    # ⭐ LẤY TÊN KHOA
        d.specialty_names = ", ".join(
            [s.name for s in d.specialties.all()]
    )


    admin_list_doctor = sorted(
        admin_list_doctor,
        key=lambda d: d.total,
        reverse=True
    )

    context = {
        'admin_list_doctor': admin_list_doctor,
        'admin_total_doctors': admin_total_doctors,
        'admin_total_appointments': admin_total_appointments,
        'admin_chart_data': json.dumps(admin_chart_data),
    }

    return render(request, 'admin/doctor-list.html', context)

def admin_patient(request):
    DB_LIST = ['specialty1', 'specialty2']

    start = request.GET.get("start")
    end = request.GET.get("end")
    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None

    all_appointments = []
    for db in DB_LIST:
        for a in Appointment.objects.using(db).all():
            a._state.db = db
            all_appointments.append(a)

    patient_map = defaultdict(list)
    for a in all_appointments:
        patient_map[a.patient_id].append(a)

    patients = Patient.objects.select_related('user').all()
    admin_list_patient = []

    for p in patients:
        appts = patient_map.get(p.id, [])

        total = len(appts)
        last_visit = max(
            [a.appointment_time for a in appts],
            default=None
        )

        admin_list_patient.append({
            'first_name': p.user.first_name,
            'last_name': p.user.last_name,
            'email': p.user.email,
            'phone_number': p.user.phone_number,
            'total': total,
            'last_visit_date': (
                localtime(last_visit).strftime('%Y-%m-%d %H:%M')
                if last_visit else None
            )
        })

    admin_list_patient.sort(key=lambda x: x['total'], reverse=True)

    first_visit = {}
    for pid, appts in patient_map.items():
        first_visit[pid] = min(a.appointment_time for a in appts)

    daily_map = defaultdict(lambda: {
        'appointments': 0,
        'patients': set(),
        'new_patients': set(),
        'returning_patients': set(),
    })

    for a in all_appointments:
        day = a.appointment_time.date()
        pid = a.patient_id

        if start_date and end_date:
            if not (start_date <= day <= end_date):
                continue

        daily_map[day]['appointments'] += 1
        daily_map[day]['patients'].add(pid)

        if a.appointment_time == first_visit.get(pid):
            daily_map[day]['new_patients'].add(pid)
        else:
            daily_map[day]['returning_patients'].add(pid)

    admin_chart_data = [
        {
            'day': day.strftime('%Y-%m-%d'),
            'appointments': data['appointments'],
            'patients': len(data['patients']),
            'new_patients': len(data['new_patients']),
            'returning_patients': len(data['returning_patients']),
        }
        for day, data in sorted(daily_map.items())
    ]
    if request.GET.get("export") == "1" and start_date and end_date:
        df_patients = pd.DataFrame(admin_list_patient)
        df_chart = pd.DataFrame(admin_chart_data)

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"BaoCao_BenhNhan_{start}_den_{end}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        with pd.ExcelWriter(response, engine="openpyxl") as writer:
            df_patients.to_excel(writer, sheet_name="Danh sách bệnh nhân", index=False)
            df_chart.to_excel(writer, sheet_name="Thống kê theo ngày", index=False)

        return response

    context = {
        'admin_list_patient': admin_list_patient,
        'admin_chart_data': json.dumps(admin_chart_data),
    }

    template = loader.get_template('admin/patient-list.html')
    return HttpResponse(template.render(context, request))

def admin_profile(request):
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
                return redirect('admin-profile')
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
                return redirect('admin-profile')
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
         
        return redirect('admin-profile')
    template = loader.get_template('admin/profile.html')
    return HttpResponse(template.render({}, request))


def admin_calendar(request, doctor_username):
    doctor = Doctor.objects.get(user__username=doctor_username)
    name_doctor = doctor.user.username
    status_summary = (
    Appointment.objects.filter(doctor_id=doctor.id)
    .values('status')
    .annotate(total=Count('id'))
)
    doctor_total_appointments = sum(s['total'] for s in status_summary)
    doctor_total_appointments_pending = next((s['total'] for s in status_summary if s['status'] == 'pending'), 0)
    doctor_total_appointments_completed = next((s['total'] for s in status_summary if s['status'] == 'completed'), 0)
    doctor_total_appointments_cancelled = next((s['total'] for s in status_summary if s['status'] == 'cancelled'), 0)

    start = request.GET.get("start")
    end = request.GET.get("end")

    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None

    status_stats = (
        Appointment.objects.filter(doctor_id=doctor.id)
        .annotate(day=TruncDay('appointment_time'))
        .values('status', 'day')
        .annotate(count=Count('id'))
        .order_by('day', 'status')
    )

    status_data = defaultdict(lambda: {
        'pending': 0,
        'confirmed': 0,
        'completed': 0,
        'cancelled': 0
    })
    for stat in status_stats:
        day_str = stat['day'].strftime('%Y-%m-%d')
        status_data[day_str][stat['status']] = stat['count']
    status_data = dict(status_data)

    daily_stats = Appointment.objects.filter(doctor_id=doctor.id, status='completed')
    if start_date and end_date:
        daily_stats = daily_stats.filter(appointment_time__date__range=[start_date, end_date])

    daily_stats = (
        daily_stats.annotate(day=TruncDay('appointment_time'))
        .values('day')
        .annotate(total_appointments=Count('id'), total_revenue=Sum('price'))
        .order_by('day')
    )

    chart_data = [
        {
            'day': stat['day'].strftime('%Y-%m-%d'),
            'appointments': stat['total_appointments'],
            'revenue': float(stat['total_revenue']) if stat['total_revenue'] else 0
        }
        for stat in daily_stats
    ]
    if request.GET.get("export") == "1" and start_date and end_date:
        appointments = Appointment.objects.filter(
    doctor_id=doctor.id,
    appointment_time__date__range=[start_date, end_date]
)


        # sheet lịch hẹn theo trạng thái
        status_stats = (
            appointments.values("appointment_time__date")
            .annotate(
                confirmed=Count("id", filter=Q(status="confirmed")),
                pending=Count("id", filter=Q(status="pending")),
                cancelled=Count("id", filter=Q(status="cancelled")),
                completed=Count("id", filter=Q(status="completed")),
            )
            .order_by("appointment_time__date")
        )
        df_status = pd.DataFrame(list(status_stats))
        df_status.rename(columns={"appointment_time__date": "Ngày"}, inplace=True)

        # sheet doanh thu
        revenue_stats = (
            appointments.values("appointment_time__date")
            .filter(status= "completed")
            .annotate(revenue=Sum("price"))
            .order_by("appointment_time__date")
        )
        df_revenue = pd.DataFrame(list(revenue_stats))
        df_revenue.rename(columns={"appointment_time__date": "Ngày", "revenue": "Doanh thu"}, inplace=True)

        # Xuất file
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"BaoCao_{name_doctor}_{start}_den_{end}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        with pd.ExcelWriter(response, engine="openpyxl") as writer:
            df_status.to_excel(writer, sheet_name="Lịch hẹn", index=False)
            df_revenue.to_excel(writer, sheet_name="Doanh thu", index=False)
        return response

    if request.method == 'POST':
        data = json.loads(request.body)
        date_str = data.get('date')
        status = data.get('status')
        DoctorSchedule.objects.update_or_create(
            doctor=doctor,
            date=date_str,
            defaults={'status': status}
        )
        return JsonResponse({'success': True})

    schedules = doctor.schedules.all()
    events = [
        {
            "title": s.get_status_display(),
            "start": s.date.isoformat(),
            "allDay": True,
            "color": "#28a745" if s.status == 'work' else "#dc3545"
        }
        for s in schedules
    ]

    context = {
        'doctor': doctor,
        'doctor_total_appointments': doctor_total_appointments,
        'doctor_total_appointments_pending': doctor_total_appointments_pending,
        'doctor_total_appointments_completed': doctor_total_appointments_completed,
        'doctor_total_appointments_cancelled': doctor_total_appointments_cancelled,
        'events': json.dumps(events),
        'chart_data': json.dumps(chart_data),
        'status_data': json.dumps(status_data),
    }
    template = loader.get_template('admin/calendar.html')
    return HttpResponse(template.render(context, request))

