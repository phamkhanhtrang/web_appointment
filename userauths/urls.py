from django.urls import path ,reverse_lazy
from userauths import views
from django.contrib.auth import views as auth_views
from userauths.forms import MySetPasswordForm
from django.conf import settings
from django.conf.urls.static import static

app_name = 'userauths'
urlpatterns = [
    path("register/", views.register_view, name='register'),    
    path("login/", views.login_view, name='login'),
    path("logout/<peanuts>/", views.logout_view, name='logout'),
    path("recover_pass/", views.recover_password, name='recover_password'),
    path('recover_pass/', auth_views.PasswordResetView.as_view(
        template_name="userauths/recover_pass.html"
    ), name="password_reset"),

    # thông báo đã gửi mail
    path('recover_pass/done/', auth_views.PasswordResetDoneView.as_view(
        template_name="userauths/password_reset_done.html"
    ), name="password_reset_done"),

    # link xác nhận từ email
     path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name="userauths/password_reset_confirm.html",
            form_class = MySetPasswordForm,
            success_url=reverse_lazy('userauths:password_reset_complete')
        ),
        name="password_reset_confirm"
    ),

    # thông báo hoàn tất reset
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name="userauths/password_reset_complete.html"
    ), name="password_reset_complete"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)