from django.conf import settings
from django.db import models

from user.models.enum import UserRole

# from ..managers import TeacherManager
from .classroom import Classroom


class Teaching(models.Model):
    """Teacher <-> class room. One row = one teacher teaches one class. Remove = delete row."""

    # objects = TeacherManager()

    classroom = models.ForeignKey(
        to=Classroom,
        db_column="classroom",
        on_delete=models.CASCADE,
        related_name="teachings",
        verbose_name="class room",
    )

    teacher = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        db_column="teacher",
        on_delete=models.CASCADE,
        related_name="teachings",
        verbose_name="teacher",
        limit_choices_to={"role": UserRole.TEACHER},
    )

    created_at = models.DateTimeField(
        verbose_name="created at",
        auto_now_add=True,
        editable=False,
    )

    class Meta:
        verbose_name = "teaching"
        verbose_name_plural = "teachings"
        constraints = [
            models.UniqueConstraint(
                fields=["classroom", "teacher"],
                name="uniq_teaching_classroom_teacher",
            )
        ]

    def __str__(self) -> str:
        return f"{self.classroom.serial} - {self.teacher}"