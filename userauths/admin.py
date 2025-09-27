from django.contrib import admin
from .models import User

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role')
# Register your models here.
admin.site.register(User, UserAdmin)