from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from django.db.models import Manager, Q

if TYPE_CHECKING:
    from user.models import User


class ClassroomManager(Manager):
    """班级 ORM 管理器。"""

    def visible_to(self, user: User):
        qs = self.get_queryset()

        if not user.is_authenticated or not user.is_active:
            return qs.none()

        if user.is_admin or user.is_staff or user.is_superuser:
            return qs

        if user.is_teacher:
            return qs.filter(
                Q(teachings__teacher=user) | Q(created_by=user)
            ).distinct()

        if user.is_student:
            return qs.filter(
                enrollments__student=user
            ).distinct()

        return qs.none()

    def search(self, keyword: str, user: Optional[User] = None):
        keyword = (keyword or "").strip()
        if not keyword:
            return self.visible_to(user) if user is not None else self.get_queryset()

        qs = self.visible_to(user) if user is not None else self.get_queryset()

        return qs.filter(
            Q(serial__icontains=keyword)
            | Q(name__icontains=keyword)
            | Q(subject__icontains=keyword)
            | Q(term__icontains=keyword)
        )


# class EnrolmentManager(Manager):
#     """学生入班 ORM 管理器"""
#
# class TeacherManager(Manager):
#     """教师 ORM 管理器"""
