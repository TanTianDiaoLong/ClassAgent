import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.services import ApiService
from classroom.models import Classroom, Enrollment, Teaching
from user.models.enum import UserRole


class ApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.admin = User.objects.create_user(
            user_id="admin001",
            email="admin001@example.com",
            password="pass",
            role=UserRole.ADMIN,
        )
        cls.teacher = User.objects.create_user(
            user_id="teacher001",
            email="teacher001@example.com",
            password="pass",
            role=UserRole.TEACHER,
        )
        cls.student = User.objects.create_user(
            user_id="student001",
            email="student001@example.com",
            password="pass",
            role=UserRole.STUDENT,
        )
        cls.outsider = User.objects.create_user(
            user_id="student002",
            email="student002@example.com",
            password="pass",
            role=UserRole.STUDENT,
        )

        cls.classroom = Classroom.objects.create(
            serial=uuid.uuid4(),
            name="Math A",
            subject="Math",
            term="2026-Fall",
            created_by=cls.admin,
        )
        Teaching.objects.create(
            classroom=cls.classroom,
            teacher=cls.teacher,
        )
        Enrollment.objects.create(
            classroom=cls.classroom,
            student=cls.student,
        )

    def auth(self, user):
        issued = ApiService.issue(user=user, name="test")
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {issued.raw}",
        )
        return issued

    def test_me(self):
        self.auth(self.student)

        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user_id"], "student001")
        self.assertEqual(response.data["role"], UserRole.STUDENT)

    def test_admin_sees_all_classrooms(self):
        self.auth(self.admin)

        response = self.client.get(reverse("classroom-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["serial"],
            str(self.classroom.serial),
        )

    def test_teacher_sees_taught_classrooms(self):
        self.auth(self.teacher)

        response = self.client.get(reverse("classroom-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_student_sees_enrolled_classrooms(self):
        self.auth(self.student)

        response = self.client.get(reverse("classroom-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_outsider_sees_no_classrooms(self):
        self.auth(self.outsider)

        response = self.client.get(reverse("classroom-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_outsider_cannot_retrieve_detail(self):
        self.auth(self.outsider)

        response = self.client.get(
            f"/api/v1/classrooms/{self.classroom.serial}/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_token(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Bearer ca_invalid.invalid",
        )

        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_revoked_token(self):
        issued = self.auth(self.student)
        ApiService.revoke(issued.key)

        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_verify_returns_user(self):
        issued = ApiService.issue(user=self.student, name="verify")

        user = ApiService.verify(issued.raw)

        self.assertEqual(user.pk, self.student.pk)
