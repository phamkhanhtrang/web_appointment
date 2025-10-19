from collections import defaultdict
import json
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
    if request.method == "POST":
        appointment_id = request.POST.get("appointment_id")
        status = request.POST.get("status")

        if appointment_id and status:
            appointment = Appointment.objects.get(id=appointment_id)
            appointment.status = status   # ✅ dùng dấu chấm
            appointment.save()
            # 
    admin_total_appointments = Appointment.objects.count()
    expired_appointment = Appointment.objects.filter(
            appointment_time__lt=now()
        ).exclude(status__in=['completed', 'cancelled'])
    expired_appointment.update(status='cancelled')
    admin_total_revenue = Appointment.objects.filter(status='completed').aggregate(total=Sum('price'))['total'] or 0
    admin_total_revenue_vnd = format_vnd(admin_total_revenue)
    
    admin_list_appointment = Appointment.objects.order_by('-appointment_time')[:10]

    
    start = request.GET.get("start")
    end = request.GET.get("end")
    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None
    
    
    daily_stats = Appointment.objects.all() \
            .annotate(day=TruncDay('appointment_time')) \
            .values('day') \
            .annotate(admin_total_appointments=Count('id'), 
                      admin_total_revenue=Sum('price'),
                      confirmed = Count('id', filter= Q(status = "confirmed")),
                      completed = Count('id', filter= Q(status = "completed")),
                      cancelled = Count('id', filter= Q(status = "cancelled")),
                      pending = Count('id', filter = Q(status = "pending")))\
            .order_by('day')

    admin_chart_data = [
            {
                'day': stat['day'].strftime('%Y-%m-%d'),
                'appointments': stat['admin_total_appointments'],
                'revenue': float(stat['admin_total_revenue']) if stat['admin_total_revenue'] else 0,
                'confirmed': stat['confirmed'],
                'pending': stat['pending'],
                'completed': stat['completed'],
                'cancelled': stat['cancelled'],
            }
            for stat in daily_stats
        ]   
    if request.GET.get("export")=="1" and start_date and end_date:
        appointments = Appointment.objects.filter(
            appointment_time__date__range = [start_date,end_date]
        ) 
        
        number_appointments = (
            appointments.values("appointment_time__date")
            .annotate(total_appointments = Count("id"))
            .order_by("appointment_time__date") 
        )
        df_appointments = pd.DataFrame(list(number_appointments))
        df_appointments.rename(columns={"appointment_time__date": "Ngày", "total_appointments": "Số lịch hẹn"}, inplace=True)
        
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
        
        response  = HttpResponse(
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"BaoCao_{start}_den_{end}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        with pd.ExcelWriter(response, engine="openpyxl") as writer:
            df_appointments.to_excel(writer, sheet_name="Số lượng cuộc hẹn theo ngày", index=False)
            df_status.to_excel(writer, sheet_name="Trạng thái lịch hẹn", index=False)
        return response
    context = {
            'admin_total_appointments': admin_total_appointments,
            'admin_total_revenue_vnd': admin_total_revenue_vnd,
            'admin_list_appointment': admin_list_appointment,
            'admin_chart_data': json.dumps(admin_chart_data)
    }
    template = loader.get_template('admin/appointment-list.html')
    return HttpResponse(template.render( context, request))
def admin_doctor(request):
    admin_total_doctors = Doctor.objects.count()
    admin_total_appointments = Appointment.objects.count()

    doctor_daily_stats = Appointment.objects.annotate(day=TruncDay('appointment_time')) \
            .values('doctor_id', 'doctor__user__first_name', 'doctor__user__last_name','day') \
            .annotate(admin_total_appointments=Count('id')) \
            .order_by('doctor_id', 'day')
            
    admin_chart_data = [
            {
                'day': stat['day'].strftime('%Y-%m-%d'),
                'appointments': stat['admin_total_appointments'],
                'doctor': f"{stat['doctor__user__first_name']} {stat['doctor__user__last_name']}",
                # 'revenue': float(stat['admin_total_revenue']) if stat['admin_total_revenue'] else 0
            }
            for stat in doctor_daily_stats
        ]
    try:
        # Nhóm theo bệnh nhân và đếm số lần đặt lịch
        admin_list_doctor = Doctor.objects.all()\
            .annotate(total=Count('id')  
                      )\
            .order_by('-total')
        # appointments = Appointment.objects.filter(doctor=doctor).order_by('-appointment_time')
        # Danh sách tất cả các lịch hẹn (để hiển thị chi tiết nếu cần)
    except Doctor.DoesNotExist:
        admin_list_doctor = []
        
    context = {
         'admin_list_doctor': admin_list_doctor,
         'admin_total_doctors': admin_total_doctors,
         'admin_total_appointments': admin_total_appointments,
         'admin_chart_data': json.dumps(admin_chart_data),
    }
    template = loader.get_template('admin/doctor-list.html')
    return HttpResponse(template.render(context, request))


def admin_patient(request):
    # --- Lấy dữ liệu filter ---
    start = request.GET.get("start")
    end = request.GET.get("end")
    start_date = parse_date(start) if start else None
    end_date = parse_date(end) if end else None

    # --- Danh sách bệnh nhân ---
    admin_list_patient = Patient.objects.all() \
        .values(
            'user__first_name',
            'user__last_name',
            'user__email',
            'user__phone_number'
        ) \
        .annotate(
            total=Count('appointments'),
            last_visit_date=Max('appointments__appointment_time')
        ) \
        .order_by('-total')

    # --- Subquery: ngày khám đầu tiên của từng bệnh nhân ---
    first_appointment = Appointment.objects.filter(
        patient_id=OuterRef('patient_id')
    ).order_by('appointment_time').values('appointment_time')[:1]

    # --- Thống kê theo ngày ---
    daily_stats = Appointment.objects.annotate(
        first_date=Subquery(first_appointment),
        day=TruncDay('appointment_time')
    ).values('day').annotate(
        admin_total_appointments=Count('id'),
        admin_total_patient=Count('patient_id', distinct=True),
        new_patients=Count('id', filter=Q(appointment_time=F('first_date'))),
        returning_patients=Count('id', filter=Q(appointment_time__gt=F('first_date')))
    ).order_by('day')

    admin_chart_data = [
        {
            'day': stat['day'].strftime('%Y-%m-%d') if stat['day'] else None,
            'appointments': stat['admin_total_appointments'],
            'patients': stat['admin_total_patient'],
            'new_patients': stat['new_patients'],
            'returning_patients': stat['returning_patients'],
        }
        for stat in daily_stats
    ]

    if request.GET.get("export") == "1" and start_date and end_date:
        df_patients = pd.DataFrame(list(admin_list_patient))
        df_chart = pd.DataFrame(admin_chart_data)

        for df in [df_patients, df_chart]:
            for col in df.select_dtypes(include=['datetimetz']).columns:
                df[col] = df[col].dt.tz_localize(None)
            for col in df.select_dtypes(include=['datetime64[ns]']).columns:
                df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M")

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"BaoCao_BenhNhan_{start}_den_{end}.xlsx"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        with pd.ExcelWriter(response, engine="openpyxl") as writer:
            df_patients.to_excel(writer, sheet_name="Danh sách bệnh nhân", index=False)
            df_chart.to_excel(writer, sheet_name="Thống kê", index=False)

        return response

    # --- Render template ---
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
        Appointment.objects.filter(doctor=doctor)
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
        Appointment.objects.filter(doctor=doctor)
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

    daily_stats = Appointment.objects.filter(doctor=doctor, status='completed')
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
            doctor=doctor,
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

