from rest_framework import serializers
from .models import Notification, UserNotification,StudentUser


class StudentUserSerializer (serializers.ModelSerializer):
    class Meta:
        model = StudentUser
        # فیلدها صریح (به‌جای __all__) تا افزودن فیلد جدید به مدل، خودکار لو نرود
        fields = (
            'id', 'student_user', 'father_name', 'phone_number', 'father_number',
            'mother_number', 'home_number', 'address', 'registration_date',
            'student_school', 'student_type', 'student_gender', 'student_grade',
            'student_time', 'student_day', 'student_status', 'student_study_date',
            'student_description',
        )

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"

class UserNotificationSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="notification.title", read_only=True)
    message = serializers.CharField(source="notification.message", read_only=True)
    is_persistent = serializers.BooleanField(source="notification.is_persistent", read_only=True)
    class Meta:
        model = UserNotification
        fields = ["id", "title", "message","is_persistent"]    