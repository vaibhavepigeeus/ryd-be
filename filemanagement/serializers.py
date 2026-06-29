from rest_framework import serializers
from .models import FileManagement
from users.models import Users
from users.serializers import MinimalUserSerializer

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Users
#         fields = ['id',
#                 'user_name',
#                 'email',
#                 'role',
#                 'status',
#                 'reporting_manager',
#                 'division',
#                 'department',
#                 'user_start_date',
#                 'user_end_date']

class FileManagementSerializer(serializers.ModelSerializer):
    # created_by = UserSerializer()
    created_by = MinimalUserSerializer(read_only=True)
    class Meta:
        model = FileManagement
        fields = '__all__'

