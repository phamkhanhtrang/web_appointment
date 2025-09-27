import json
from django.contrib import messages

from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from userauths.models import Appointment, Prescription
from userauths.models import Doctor,User
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
        
        total_patients = Appointment.objects.filter(doctor=doctor).values('patient').distinct().count()

        total_appointments = Appointment.objects.filter(doctor=doctor, ).count()

        total_revenue = Appointment.objects.filter(doctor=doctor, 
                                                   status = 'completed').aggregate(total=Sum('price'))['total'] or 0
        total_revenue_vnd = format_vnd(total_revenue)

        # Thống kê theo bệnh nhân
        patient_stats = Appointment.objects.filter(doctor=doctor) \
            .values('patient__user__username') \
            .annotate(total=Count('id')) \
            .order_by('-total')

        # Tất cả lịch hẹn
        appointments = Appointment.objects.filter(doctor=doctor).order_by('-appointment_time')

        # Biểu đồ: cuộc hẹn và doanh thu theo tháng
        monthly_stats = Appointment.objects.filter(doctor=doctor, status='completed') \
            .annotate(month=TruncMonth('appointment_time')) \
            .values('month') \
            .annotate(total_appointments=Count('id'), total_revenue=Sum('price')) \
            .order_by('month')

        chart_data = [
            {
                'month': stat['month'].strftime('%Y-%m'),
                'appointments': stat['total_appointments'],
                'revenue': float(stat['total_revenue']) if stat['total_revenue'] else 0
            }
            for stat in monthly_stats
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
        'chart_data': json.dumps(chart_data),  # Gửi sang template cho JS
    }

    return render(request, 'doctor/index.html', context)
@role_required('doctor')
def appointment_view(request):
    try:
        doctor = request.user.doctor_profile
        # Huỷ các lịch hẹn quá hạn chưa hoàn thành
        expired_appointment = Appointment.objects.filter(
            doctor=doctor,
            appointment_time__lt=now()
        ).exclude(status__in=['completed', 'cancelled'])
        expired_appointment.update(status='cancelled')

        # Danh sách lịch hẹn
        appointments = Appointment.objects.filter(doctor=doctor).order_by('-appointment_time') \
    .select_related('patient__user') \
    .prefetch_related(
        'prescription__details'
    )
        # Cập nhật trạng thái lịch hẹn nếu có POST
        if request.method == 'POST':
            appointment_id = request.POST.get('appointment_id')
            new_status = request.POST.get('status')
            appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
            appointment.status = new_status
            appointment.save()
            # messages.success(request, "Cập nhật trạng thái thành công.")

    except Doctor.DoesNotExist:
        appointments = []

    context = {'appointments': appointments}
    return render(request,'doctor/appointment-list.html', context)
@role_required('doctor')
def patient_view(request):
    try:
        doctor = request.user.doctor_profile
        # Nhóm theo bệnh nhân và đếm số lần đặt lịch
        patient_stats = (
            Appointment.objects.filter(doctor=doctor)
            .values( 'patient__user__phone_number','patient__user__first_name','patient__user__last_name')
            .annotate(
                total=Count('id'),
                total_price=Sum('price')
            )
            .order_by('-total')
        )
        for stat in patient_stats:
            stat['total_price_vnd'] = format_vnd(stat['total_price'])

        # Danh sách tất cả các lịch hẹn (để hiển thị chi tiết nếu cần)
        appointments = Appointment.objects.filter(doctor=doctor).order_by('-appointment_time')
    except Doctor.DoesNotExist:
        appointments = []
        patient_stats = []
    context = {
        # 'appointments': appointments,
        'patient_stats': patient_stats,
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
    appointments = Appointment.objects.filter(doctor=doctor, status__in=['confirmed','completed', 'pending'])
     # Chuyển đổi dữ liệu lịch hẹn sang định dạng JSON cho FullCalendar
    events = []
    for a in appointments:
        events.append({
           'id': a.id,
            'title': a.patient.user.get_full_name(),
            'start': a.appointment_time.replace(tzinfo=None).isoformat(),
            'status': a.status,
            'patient_name': a.patient.user.get_full_name(),
           
        })
    
    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        diagnosis = request.POST.get('diagnosis')
        note = request.POST.get('note')
        appointment = get_object_or_404(Appointment, id=appointment_id)
        doctor = appointment.doctor
        patient = appointment.patient
        
        prescription = Prescription.objects.create(
            appointment=appointment,
            doctor=doctor,
            patient=patient,
            diagnosis=diagnosis,
            note=note
        )
        medicine_names = request.POST.getlist('medicine_name[]')
        dosages = request.POST.getlist('dosage[]')
        usages = request.POST.getlist('usage[]')
        quantities = request.POST.getlist('quantity[]')
        
        for i in range(len(medicine_names)):
            if medicine_names[i].strip():
                prescription.details.create(
                    medication_name=medicine_names[i],
                    dosage=dosages[i],
                    usage=usages[i],
                    quantity=int(quantities[i]) if i < len(quantities) and quantities[i].isdigit() else 1
                )
        messages.success(request, "Kê đơn thành công.")
        return redirect('calendar_view')
    template = loader.get_template('doctor/calendar.html')
    return HttpResponse(template.render({'events_json': json.dumps(events)}, request))