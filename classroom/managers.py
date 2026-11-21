from django.db.models import Manager
from django.db.models import Q

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from user.models import User

class ClassroomManager(Manager):
    """班级ORM管理器"""

    def visible_to(self, user:"User"):
        if not user.is_authenticated:
            return self.none()

        if user.is_admin or user.is_staff or user.is_superuser:
            return self

        if user.is_teacher:
            return self.filter(
                Q(teachings__teacher=user) | Q(created_by=user)
            ).distinct()

        if user.is_student:
            return self.filter(
                enrollments__student=user
            ).distinct()

        return self.none()

    def search(self, keyword: str, user: Optional["User"] = None):
        keyword = (keyword or "").strip()
        if not keyword:
            return self

        if user:
            sq = self.visible_to(user)
        else:
            sq = self

        return sq.filter(
            Q(serial__icontains=keyword)
            | Q(subject__icontains=keyword)
            | Q(term__icontains=keyword)
        )

# class EnrolmentManager(Manager):
#     """学生入班ORM管理器"""
#
# class TeacherManager(Manager):
#     """教师ORM管理器"""