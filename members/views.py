# members/views.py
from datetime import datetime
from django.contrib import messages
from django.http import HttpResponse
from django.template import loader
from userauths.models import Doctor
from userauths.models import Patient
from userauths.models import Appointment,Appointment,DoctorSchedule,User
from django.shortcuts import render, redirect,get_object_or_404
from userauths.decorators import role_required
from  django.conf import settings
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from django.template.loader import render_to_string
from django.core.mail import send_mail
import json
from django.utils.timezone import localtime
from django.db import IntegrityError



# @role_required('patient')
def members(request):
     doctors = Doctor.objects.select_related('user').all()  # dùng object thay vì .values()
     template = loader.get_template('members/index.html')
     context = {
        'list_doctor': doctors
     }
     return HttpResponse(template.render(context, request))
@role_required('patient')
def about(request):
    template = loader.get_template('members/about.html')  
    return HttpResponse(template.render({}, request))
@role_required('patient')
def service(request):
    template = loader.get_template('members/service.html')  
    return HttpResponse(template.render({}, request))
# @role_required('patient')
# def appointment(request,name):
#     doctors = Doctor.objects.get(user__username=name)
    
#     template = loader.get_template('members/appointment.html') 
#     context = {
#         'doctor_name': doctors
#     }
    return HttpResponse(template.render(context, request))
@role_required('patient')
def profile(request):
    user =request.user
    patient = request.user.patient_profile 
    
    if request.method == 'POST':
        username = request.POST.get('username')
        full_name = request.POST.get('fullname')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if username and username != user.username:
            if User.objects.filter(username=username).exclude(pk=user.pk).exists():
                messages.error(request, "Tên đăng nhập đã được sử dụng, vui lòng chọn tên khác.")
                return redirect('profile')
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
                return redirect('profile')
            user.email = email

        if password:
            user.set_password(password)  # luôn hash
            
        try:
            user.save()
            messages.success(request, "Cập nhật thông tin thành công!")
        except IntegrityError:
            messages.error(request, "Có lỗi xảy ra, vui lòng thử lại.")
         
        return redirect('profile')
        
    try:       
        appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_time')
    except Patient.DoesNotExist:
        appointments = []
    

    context = {'appointments': appointments,
               'patient': patient }
    return render(request, 'members/profile.html', context)


def book_appointment_view(request, doctor_username):     
    doctor = Doctor.objects.get(user__username=doctor_username)
    doctor_schedule = DoctorSchedule.objects.filter(doctor=doctor)
    appointments = Appointment.objects.filter(doctor=doctor, status__in = ['completed', 'pending','confirmed'] )
    
    patient = request.user.patient_profile

    if request.method == 'POST':
        appointment_time_str = request.POST.get('appointment_time')
        try:
            # Giả sử format bạn dùng là "HH:MM - dd/mm/yyyy"
            appointment_time = datetime.strptime(appointment_time_str, "%H:%M - %d/%m/%Y")
        except (ValueError, TypeError):
            messages.error(request, 'Thời gian đặt lịch không hợp lệ.')
            return redirect('appointment', doctor_username=doctor_username)

        notes = request.POST.get('notes', '')
        payment_method = request.POST.get('payment_method')

        # Tạo lịch hẹn
        appointment = Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            appointment_time=appointment_time,
            notes=notes,
            price=doctor.price,
            payment_method=payment_method       
        )        
        if payment_method == "momo":
           return redirect('payment-complete', appointment_id=appointment.id)
             
    #     subject = f'Thông tin thanh toán lịch hẹn #{appointment.id}'
    #     message = render_to_string('members/payment_success.html', {
    #     'appointment': appointment,
    #     'doctor': appointment.doctor,
    #     'patient': appointment.patient,
    # })
    #     recipient_list = [appointment.patient.user.email]
    #     send_mail(
    #     subject,
    #     message,
    #     None,  # sẽ dùng DEFAULT_FROM_EMAIL
    #     recipient_list,
    #     fail_silently=False,
    # ) 

        messages.success(request, 'Đặt lịch thành công!')
        
        return redirect('appointment', doctor_username=doctor_username)

    booked_times = {}
    for a in appointments: 
        local_dt = localtime(a.appointment_time)  # đổi về giờ local
        date_str = local_dt.strftime("%Y-%m-%d")
        time_str = local_dt.strftime("%H:%M")
        booked_times.setdefault(date_str, []).append(time_str)
    data = []
    for s in doctor_schedule:
        data.append({
            "date": s.date.strftime("%Y-%m-%d"),
            "status": s.status,
            "booked_times": booked_times.get(s.date.strftime("%Y-%m-%d"), []),
        })
    
    return render(request, 'members/appointment.html', {
        'doctor_name': doctor,
        'user': request.user,
        'schedules': json.dumps(data), 
    })

def payment_complete_view(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    host = request.get_host()
    status = request.GET.get('status')

    # Nếu appointment đã bị xóa thì không hiển thị invoice nữa
    if not appointment:
        return render(request, 'members/payment-complete.html', {
            'appointment': None,
            'payment_status': 'failed',
        })

    # Chuẩn bị thông tin thanh toán PayPal
    usd_amount = round(appointment.price / 24000, 2)  # VND → USD
    paypal_dict = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': f"{usd_amount:.2f}",
        'item_name': f"Appointment with Dr. {appointment.doctor.user.get_full_name()}",
        'invoice': f"INV-{appointment.id}",
        'currency_code': 'USD',
        'notify_url': f"http://{host}{reverse('paypal-ipn')}",
        'return_url': f"http://{host}{reverse('payment-complete', args=[appointment.id])}?status=completed",
        'cancel_return': f"http://{host}{reverse('payment-complete', args=[appointment.id])}?status=failed",}
    paypal_payment_button = PayPalPaymentsForm(initial=paypal_dict)

    # Xử lý theo trạng thái thanh toán
    if status == 'completed':
        appointment.status = "completed"
        appointment.save()

        # Gửi mail xác nhận
        subject = f'Thông tin thanh toán lịch hẹn #{appointment.id}'
        message = render_to_string('members/payment_success.html', {
            'appointment': appointment,
            'doctor': appointment.doctor,
            'patient': appointment.patient,
        })
        recipient_list = [appointment.patient.user.email]
        send_mail(subject, message, None, recipient_list, fail_silently=False)

        payment_status = "confirmed"

    elif status == 'failed':
        appointment.delete()
        return render(request, 'members/payment-failed.html', {
            # 'appointment': None,
            # 'payment_status': 'failed',
        })

    else:
        # Mới pending, chưa thanh toán
        payment_status = "pending"

    return render(request, 'members/payment-complete.html', {
        'paypal_payment_button': paypal_payment_button,
        'appointment': appointment,
        'payment_status': payment_status,
    })

def payment_failed_view(request):
    return render(request, 'members/payment-failed.html')