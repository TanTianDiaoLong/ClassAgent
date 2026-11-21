from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from classroom.models import Classroom

from .serializers import ClassroomSerializer, UserSerializer


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ClassroomViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ClassroomSerializer
    lookup_field = "serial"

    def get_queryset(self):
        return (
            Classroom.objects
            .visible_to(self.request.user)
            .select_related("created_by")
            .order_by("-created_at")
        )
