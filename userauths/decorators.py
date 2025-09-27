from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied


def role_required(required_role):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            # Kiểm tra đã đăng nhập chưa
            if not request.user.is_authenticated:
                return redirect('login')
            # Kiểm tra đúng vai trò chưa
            if request.user.role != required_role:
                raise PermissionDenied  # hoặc redirect('no_permission')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator