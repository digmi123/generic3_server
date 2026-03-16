from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Staff, StaffClinic, Patient, PatientClinic, PatientDoctor


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Role & 2FA', {'fields': ('role', 'is_2fa_enabled')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    search_fields = ['email', 'first_name', 'last_name']
    filter_horizontal = ['groups', 'user_permissions']


admin.site.register(Staff)
admin.site.register(StaffClinic)
admin.site.register(Patient)
admin.site.register(PatientClinic)
admin.site.register(PatientDoctor)
