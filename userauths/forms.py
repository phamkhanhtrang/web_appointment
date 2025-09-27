from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from userauths.models import Doctor
from django.contrib.auth.forms import SetPasswordForm


User = get_user_model()

class UserRegisterForm(UserCreationForm):
    username = forms.CharField(label="Tên người dùng")
    phone_number = forms.CharField(label="SĐT")
    password1 = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Xác nhận mật khẩu", widget=forms.PasswordInput)
    avatar = forms.ImageField(label="Ảnh đại diện", required=False)  # ✅ Sửa tại đây

    user_config = forms.ChoiceField(label="Vai trò", choices=[('Patient', 'Bệnh nhân'), ('Doctor', 'Bác sĩ')])
    SPECIALITY_CHOICES = [
        ('Implant', 'Implant nha khoa'),
        ('cosmetic dentistry', 'Nha khoa thẩm mỹ'),
        ('dental restoration', 'Phục hình răng'),
        ('root canal treatment', 'Điều trị tủy răng'),
        ('Dental surgery', 'Phẫu thuật răng'),
    ]
    speciality = forms.ChoiceField(choices=SPECIALITY_CHOICES, required=False, label='Chuyên khoa')
    price = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label='Giá khám bệnh')

    class Meta:
        model = User
        fields = ('username', 'phone_number', 'email', 'avatar', 'user_config', 'speciality', 'price', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user_config = self.cleaned_data.get('user_config')

        user.role = 'doctor' if user_config == 'Doctor' else 'patient'

        if commit:
            user.save()
            if user.role == 'doctor':
                Doctor.objects.create(
                    user=user,
                    specialization=self.cleaned_data.get('speciality'),
                    price=self.cleaned_data.get('price')
                )

        return user
    
class MySetPasswordForm(SetPasswordForm):
    error_messages = {
        "password_mismatch": ("Hai mật khẩu không khớp."),
    }
    new_password1 = forms.CharField(
        label= "Mật khẩu mới",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    new_password2 = forms.CharField(
        label= "Xác nhận mật khẩu mới",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

