from django.contrib.auth import get_user_model
from rest_framework import serializers

from classroom.models import Classroom

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("user_id", "display_name", "role")
        read_only_fields = fields

    def get_display_name(self, obj):
        return obj.display_name()


class ClassroomSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Classroom
        fields = (
            "serial",
            "name",
            "subject",
            "term",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
