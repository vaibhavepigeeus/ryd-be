from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager
from django.contrib.auth.models import AbstractBaseUser
from documents.models import *
from documents.utils.encryption_util import encrypt_text, decrypt_text, is_decrypted


class UserPermissions(models.Model):
    permissions_list = models.JSONField()
    role = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)


class Users(AbstractBaseUser):
    user_name = models.CharField(max_length=100)
    email = models.EmailField(default=None, unique=True)
    role = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    reporting_manager = models.ForeignKey('Users', on_delete=models.CASCADE, related_name="userss", null=True, blank=True)
    division = models.ForeignKey(Entity, on_delete=models.CASCADE, null=True, blank=True)
    department = models.CharField(max_length=100)
    user_permissions = models.ForeignKey(UserPermissions, on_delete=models.CASCADE, null=True, blank=True)
    user_start_date = models.DateTimeField(null=True)
    user_end_date = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    password_updated_at = models.DateField(null=True, blank=True)

    def get_decrypted_email(self):
        try:
            if is_decrypted(self.email):
                return self.email
            return decrypt_text(self.email)
        except Exception as e:
            return self.email

    def get_decrypted_value(self, value):
        try:
            if is_decrypted(value):
                return value
            return decrypt_text(value)
        except Exception as e:
            return value
        
    def has_perm(self, perm, obj=None):
        return self.is_active and self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_active and self.is_superuser

    def save(self, *args, **kwargs):
        if self.pk:
            # Check if the email field has changed
            original = Users.objects.get(pk=self.pk)
            if original.email != self.email and is_decrypted(self.email):
                self.email = encrypt_text(self.email)
        else:
            if is_decrypted(self.email):
                self.email = encrypt_text(self.email)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user_name

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()


class ResetTokens(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, default=1)
    resetToken = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.user.email)


class UserPasswordHistory(models.Model):
    password = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.password)


class UserAuditHistory(models.Model):
    user = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True)
    ip = models.GenericIPAddressField(null=True)
    created_datetime = models.DateTimeField(auto_now_add=True, null=True)
    api_url = models.URLField(max_length=200, null=True)
    api_method = models.CharField(max_length=10, null=True)
    response_status_code = models.PositiveSmallIntegerField(null=True)
    payload = models.JSONField(null=True)
    response = models.JSONField(null=True)

    def __str__(self):
        return str(self.api_url)
    
class UserSessionManagement(models.Model):
    user = models.ForeignKey('Users', on_delete=models.CASCADE, null=True)
    isLoggedIn = models.BooleanField(default=False)
    logged_in_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)