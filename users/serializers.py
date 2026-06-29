from datetime import timedelta

from django.contrib.auth.hashers import check_password
from documents.utils.encryption_util import decrypt_text

# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from rest_framework_simplejwt.tokens import RefreshToken
from knox.models import AuthToken
from rest_framework import serializers

from .models import UserPermissions, Users
from documents.models import CommonAudit
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

class MinimalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id', 'user_name']


class UserSerializer(serializers.ModelSerializer):
    decrypted_email = serializers.SerializerMethodField()
    reporting_manager = MinimalUserSerializer(read_only=True)

    class Meta:
        model = Users
        # fields = "__all__"
        exclude = ['email', 'password']
        depth = 1

    def get_decrypted_email(self, obj):
        email = obj.get_decrypted_email()
        try:
            user_part, domain_part = email.split("@", 1)
            # if user_part:  # Ensure there's at least one character before '@'
            #     masked_email = f"{user_part[0]}***@{domain_part}"
            # else:
            masked_email = f"***@{domain_part}"
        except:
            masked_email = email  # In case the email is not in standard format
        return masked_email

    def get_masked_value(self, obj, value):
        updated_value = obj.get_decrypted_value(value)
        try:
            user_part, domain_part = updated_value.split("@", 1)
            masked_email = f"***@{domain_part}"
        except:
            masked_email = updated_value
        return masked_email

    def to_representation(self, instance):
        data = super().to_representation(instance)
        audit_list = []
        for row in CommonAudit.objects.filter(record_id=instance.pk).order_by("-id"):
            if row.field_name == "email":
                try:
                    old_value = self.get_masked_value(instance, row.old_value)
                    new_value = self.get_masked_value(instance, row.new_value)
                except Exception as e:
                    logger.info(f"error in user serializer: {e}")
            else:
                old_value = row.old_value
                new_value = row.new_value
                
            audit_list.append({
                "field_name": row.field_name, 
                "old_value": old_value, 
                "new_value": new_value, 
                "changed_by": row.changed_by.user_name,
                "current_time": datetime.strftime(row.current_time, "%Y-%m-%d %H:%M:%S"),
                "previous_time": datetime.strftime(row.previous_time, "%Y-%m-%d %H:%M:%S"),
                "event_type": row.event_type,
                "id": row.id
            })
        data['user_audit_data'] = audit_list

        return data


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()
    user = serializers.IntegerField(required=False)

    @classmethod
    def get_token(cls, user):
        # Access token expires in 1 hour
        instance_access_token, access_token = AuthToken.objects.create(
            user=user, 
            expiry=timedelta(hours=1)
        )

        # Refresh token expires in 1 day
        instance_refresh_token, refresh_token = AuthToken.objects.create(
            user=user, 
            expiry=timedelta(days=1)    
        )

        return access_token, refresh_token
    
    def validate(self, data):
        # Validate data using superclass method (assuming it performs validation)
        data = super().validate(data)

        # Try to get the user using email, handle potential exceptions
        try:
            user_obj = Users.objects.get(id=data['user'])
        except Users.DoesNotExist:
            raise serializers.ValidationError('Invalid email')

        decrypted_password = decrypt_text(data['password'])
        
        # Perform password check using Django's check_password function
        check_user_password = check_password(decrypted_password, user_obj.password)

        if not check_user_password:
            raise serializers.ValidationError('Invalid password')

        # Add user information and tokens to the validated data
        data['access'], data['refresh'] = self.get_token(user_obj)
        data['username'] = user_obj.user_name
        data['email'] = user_obj.email
        data['role'] = user_obj.role
        data['status'] = user_obj.status
        data['user_id'] = user_obj.id
        del data['password']
        return data


class ResetPasswordSerializer(serializers.Serializer):
    model = Users

    """
    Serializer for password change endpoint.
    """
    email = serializers.CharField(required=True)


class UserPermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPermissions
        fields = '__all__'
