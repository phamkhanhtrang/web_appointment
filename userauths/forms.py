from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from userauths.models import Doctor, Specialty
from django.contrib.auth.forms import SetPasswordForm


User = get_user_model()

class UserRegisterForm(UserCreationForm):
    username = forms.CharField(label="Tên người dùng")
    phone_number = forms.CharField(label="SĐT")
    password1 = forms.CharField(label="Mật khẩu", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Xác nhận mật khẩu", widget=forms.PasswordInput)
    avatar = forms.ImageField(label="Ảnh đại diện", required=False)

    user_config = forms.ChoiceField(
        label="Vai trò",
        choices=[('Patient', 'Bệnh nhân'), ('Doctor', 'Bác sĩ')]
    )


    speciality = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.none(),    # tạm thời để none
        required=False,
        label='Chuyên khoa'
    )

    price = forms.DecimalField(
        max_digits=10, decimal_places=2,
        required=False,
        label='Giá khám bệnh'
    )

    class Meta:
        model = User
        fields = (
            'username', 'phone_number', 'email', 'avatar',
            'user_config', 'speciality', 'price',
            'password1', 'password2'
        )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 💥 Lấy chuyên khoa từ DB
        self.fields['speciality'].queryset = Specialty.objects.all()

    def save(self, commit=True):
        user = super().save(commit=False)

        # Gán role
        user_config = self.cleaned_data.get('user_config')
        user.role = 'doctor' if user_config == 'Doctor' else 'patient'

        if commit:
            user.save()

            # Nếu là bác sĩ → tạo Doctor + specialties
            if user.role == 'doctor':
                doctor = Doctor.objects.create(
                    user=user,
                    price=self.cleaned_data.get('price')
                )

                specialties = self.cleaned_data.get('speciality')
                for s in specialties:
                    specialty_obj, created = Specialty.objects.get_or_create(name=s)
                    doctor.specialties.add(specialty_obj)

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

