from rest_framework import serializers
from . import models


class StudentUserSerializer (serializers.ModelSerializer):
    class Meta:
        model = models.StudentUser
        fields = "__all__"

    