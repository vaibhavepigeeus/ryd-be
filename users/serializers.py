from django.contrib.auth.hashers import check_password
from rest_framework import serializers

from .constants import UserRole
from .models import CoachCoachee, UserPermissions, Users
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
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        from .auth_helpers import find_user_by_email

        email = data["email"].lower()
        user = find_user_by_email(email, require_active=True)

        if not user:
            inactive_user = find_user_by_email(email, require_active=False)
            if inactive_user and inactive_user.status == "Inactive":
                raise serializers.ValidationError("Your account is inactive. Please contact support.")
            raise serializers.ValidationError("No account found with this email address.")

        if not check_password(data["password"], user.password):
            raise serializers.ValidationError("Invalid password.")

        data["user"] = user
        return data


class RegisterSerializer(serializers.Serializer):
    user_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()

    def validate_email(self, value):
        from .auth_helpers import find_user_by_email

        if find_user_by_email(value.lower(), require_active=False):
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        from .utils import generate_combination, send_welcome_password_email

        password = generate_combination()
        user = Users.objects.create_user(
            email=validated_data["email"],
            password=password,
            user_name=validated_data["user_name"],
            role=UserRole.COACHEE,
            status="Active",
        )
        send_welcome_password_email(validated_data["email"], password)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    coach_id = serializers.IntegerField(source="reporting_manager_id", read_only=True)
    coach_name = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = [
            "id",
            "user_name",
            "email",
            "role",
            "status",
            "coach_id",
            "coach_name",
        ]

    def get_email(self, obj):
        return obj.get_decrypted_email()

    def get_coach_name(self, obj):
        return obj.reporting_manager.user_name if obj.reporting_manager else None


class CoachListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ["id", "user_name"]


class CoachCoacheeListSerializer(serializers.ModelSerializer):
    coachee_id = serializers.IntegerField(source="coachee.id", read_only=True)
    user_name = serializers.CharField(source="coachee.user_name", read_only=True)
    email = serializers.SerializerMethodField()
    status = serializers.CharField(source="coachee.status", read_only=True)
    linked_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = CoachCoachee
        fields = ["coachee_id", "user_name", "email", "status", "linked_at"]

    def get_email(self, obj):
        return obj.coachee.get_decrypted_email()


class CoachCreateCoacheeSerializer(serializers.Serializer):
    user_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()

    def validate_email(self, value):
        from .auth_helpers import find_user_by_email

        if find_user_by_email(value.lower(), require_active=False):
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        from django.utils import timezone

        from .utils import generate_combination, send_welcome_password_email

        coach = self.context["coach"]
        password = generate_combination()
        coachee = Users.objects.create_user(
            email=validated_data["email"],
            password=password,
            user_name=validated_data["user_name"],
            role=UserRole.COACHEE,
            status="Active",
            reporting_manager=coach,
            user_start_date=timezone.now(),
        )
        link = CoachCoachee.objects.create(coach=coach, coachee=coachee)
        send_welcome_password_email(validated_data["email"], password)
        return link


class CoachLinkCoacheeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        from .auth_helpers import find_user_by_email

        email = value.lower()
        coach = self.context["coach"]
        coachee = find_user_by_email(email, require_active=True)

        if not coachee:
            inactive = find_user_by_email(email, require_active=False)
            if inactive and inactive.status == "Inactive":
                raise serializers.ValidationError("This user account is inactive.")
            raise serializers.ValidationError("No coachee found with this email address.")

        if coachee.role != UserRole.COACHEE:
            raise serializers.ValidationError("This email belongs to a user who is not a coachee.")

        if coachee.id == coach.id:
            raise serializers.ValidationError("You cannot add yourself as a coachee.")

        existing_link = CoachCoachee.objects.filter(coachee=coachee).select_related("coach").first()
        if existing_link:
            if existing_link.coach_id == coach.id:
                raise serializers.ValidationError("This coachee is already linked to your account.")
            raise serializers.ValidationError("This coachee already has a coach assigned.")

        self.context["coachee"] = coachee
        return email

    def create(self, validated_data):
        coach = self.context["coach"]
        coachee = self.context["coachee"]
        link = CoachCoachee.objects.create(coach=coach, coachee=coachee)
        if coachee.reporting_manager_id is None:
            coachee.reporting_manager = coach
            coachee.save(update_fields=["reporting_manager"])
        return link


class CoachUpdateCoacheeSerializer(serializers.Serializer):
    user_name = serializers.CharField(max_length=100)

    def validate_user_name(self, value):
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError("Name cannot be empty.")
        return trimmed


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
