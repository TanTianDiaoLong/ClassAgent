import uuid
from typing import Optional
from user.models import User
from classroom.models import Classroom, Enrollment, Teaching


class ClassroomService:
    """classroom 业务层"""
    classroom_model = Classroom
    enrollment_model = Enrollment
    teaching_model = Teaching

    def create_classroom(self, **kwargs):
        new_classroom = self.classroom_model(**kwargs)
        new_classroom.serial = uuid.uuid4()
        new_classroom.save()

    def delete_classroom(self, classroom: Optional[Classroom] = None, classroom_id: str = "", ):
        if not classroom_id and not classroom:
            raise ValueError
        if classroom:
            classroom.delete()
            return

        if classroom_id:
            classroom = self.classroom_model.objects.filter(serial=classroom_id)
            classroom.delete()

    def get_classroom_by_id(self, classroom_id) -> Optional[Classroom]:
        return self.classroom_model.objects.first(serial=classroom_id)

    def get_classroom_by_name(self, classroom_name) -> Optional[Classroom]:
        try:
            self.classroom_model.objects.get(serial=classroom_name)
        except self.classroom_model.DoesNotExist:
            return None

    def student_enroll(self, student: User, classroom: Classroom) -> Enrollment:
        new_enrollment = self.enrollment_model(student=student, classroom = classroom)
        new_enrollment.save()
        return new_enrollment

