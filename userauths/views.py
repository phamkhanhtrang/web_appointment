from django.template import loader
from django.shortcuts import redirect, render
from django.conf import settings
from userauths.forms import UserRegisterForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages  
from .models import Patient, Specialty
from .models import Doctor
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy

User = get_user_model()


# # Create your views here.

@login_required
def dashboard_view(request):
    user = request.user

    if user.role == 'doctor':
        return render(request, 'dashboard/doctor.html', {'user': user})

    elif user.role == 'patient':
        return render(request, 'dashboard/patient.html', {'user': user})

    else:
        return render(request, 'dashboard/unknown.html')

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)

            # Xác định role
            user_config = form.cleaned_data.get('user_config')
            user.role = 'doctor' if user_config == 'Doctor' else 'patient'

            # Avatar
            user.avatar = form.cleaned_data.get('avatar')
            user.save()

            # Nếu là bác sĩ
            if user.role == 'doctor':
                doctor = Doctor.objects.create(
                    user=user,
                    price=form.cleaned_data.get('price')
                )

                # Lấy danh sách các chuyên khoa được chọn
                specialties = form.cleaned_data.get('speciality')  # list

                # Lưu vào bảng Specialty và liên kết ManyToMany
                for s in specialties:
                    specialty_obj, created = Specialty.objects.get_or_create(name=s)
                    doctor.specialties.add(specialty_obj)

            # Nếu là bệnh nhân
            else:
                Patient.objects.create(
                    user=user,
                    phone_number=form.cleaned_data.get('phone_number')
                )

            return redirect('/login')

    else:
        form = UserRegisterForm()

    return render(request, 'userauths/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful")
            # Chuyển hướng theo vai trò
            if user.role == 'doctor':
                return redirect('/doctor')  # bạn tạo route này
            elif user.role == 'patient':
                return redirect('/')  # bạn tạo route này
            else:
                return redirect('/admin')
        else:
            messages.error(request, "Sai tên đăng nhập hoặc mật khẩu")
    return render(request, 'userauths/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Bạn đã đăng xuất")
    return redirect("userauths:register")
def recover_password(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='userauths/password_reset_email.html',  
                subject_template_name='userauths/password_reset_subject.txt',
                from_email=None,
            )
            messages.success(request, "Liên kết khôi phục đã được gửi tới email của bạn.")
            return redirect('userauths:login')
        else:
            messages.error(request, "Email không hợp lệ hoặc không tồn tại.")
    else:
        form = PasswordResetForm()
    return render(request, 'userauths/recover_pass.html', {"form": form})
