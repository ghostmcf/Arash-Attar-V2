from rest_framework import serializers
from .models import Notification, UserNotification,StudentUser


class StudentUserSerializer (serializers.ModelSerializer):
    class Meta:
        model = StudentUser
        fields = "__all__"

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