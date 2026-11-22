from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render

from classroom.models import Classroom, Enrollment
from user.models import User
from user.models.enum import UserRole
from django.db.models import Count

from .utils import audience_of, ROLE_LABEL

class DashboardView(LoginRequiredMixin, View):
    """访问 /dashboard/ 时执行。

    第一个参数 LoginRequiredMixin 的作用是：没登录就直接跳去登录页，
    不会执行下面任何一行代码。跳转地址取 settings.LOGIN_URL。
    """

    template_name = "dashboard.html"

    def get(self, request):
        audience = audience_of(request.user)
        user = request.user

        context = {
            "audience": audience,
            "role_label": ROLE_LABEL[audience],
            "page_title": "工作台 · ClassAgent",
        }

        # 三种角色，三种数据口径。拆成三个小方法，避免一个函数几百行。
        if audience == "admin":
            context.update(self._admin_data())
        elif audience == "teacher":
            context.update(self._teacher_data(user))
        else:
            context.update(self._student_data(user))

        # 底部"账户与设置"面板，三种角色共用。
        context["account_rows"] = [
            ("学号 / 工号", user.user_id),
            ("姓名", user.display_name()),
            ("邮箱", user.email or "—"),
            ("角色", ROLE_LABEL[audience]),
        ]
        return render(request, self.template_name, context)

    # -- 以下三个方法返回的字典，会被 update() 合并进 context ---------------

    @staticmethod
    def _admin_data() -> dict:
        """管理员：看全站。"""
        classes = (
            Classroom.objects.prefetch_related("teachings__teacher")
            .annotate(student_count=Count("enrollments"))
            .order_by("serial")
        )
        return {
            "headline": "系统总览",
            "lede": "教学班、成员与选课关系的最新汇总。",
            "cards": [
                {"label": "教学班", "value": Classroom.objects.count(), "hint": "全部"},
                {"label": "教师", "value": User.objects.filter(role=UserRole.TEACHER).count(), "hint": "账号数"},
                {"label": "学生", "value": User.objects.filter(role=UserRole.STUDENT).count(), "hint": "账号数"},
                {"label": "选课记录", "value": Enrollment.objects.count(), "hint": "条"},
            ],
            "classes": classes,
            "show_counts": True,
            "show_teachers": True,
            "table_title": "全部教学班",
            "colspan": 5,
            "empty_hint": "还没有教学班，可以先到 /admin/ 建一个。",
        }

    @staticmethod
    def _teacher_data(user) -> dict:
        """教师：只看自己教的班。

        filter(teachings__teacher=user) 的意思是：
        顺着 ClassRoom -> Teaching -> teacher 这条关系，筛出教师是本人的班级。
        双下划线 __ 表示"穿过一层关联"。
        """
        mine = Classroom.objects.filter(teachings__teacher=user)
        classes = (
            mine.prefetch_related("teachings__teacher")
            .annotate(student_count=Count("enrollments", distinct=True))
            .order_by("serial")
        )
        enrolled = Enrollment.objects.filter(classroom__teachings__teacher=user)
        return {
            "headline": "我的教学工作台",
            "lede": "你任教的班级与学生规模。",
            "cards": [
                {"label": "任教班级", "value": mine.distinct().count(), "hint": "个"},
                {"label": "学生总数", "value": enrolled.values("student").distinct().count(), "hint": "去重后"},
                {"label": "选课记录", "value": enrolled.count(), "hint": "条"},
            ],
            "classes": classes,
            "show_counts": True,
            "show_teachers": True,
            "table_title": "我的教学班",
            "colspan": 5,
            "empty_hint": "还没有关联的教学班，请联系管理员安排任课。",
        }

    @staticmethod
    def _student_data(user) -> dict:
        """学生：只看自己选的班。"""
        mine = Enrollment.objects.filter(student=user)
        classes = (
            Classroom.objects.filter(enrollments__student=user)
            .prefetch_related("teachings__teacher")
            .order_by("serial")
        )

        # 我所有班里的老师，去重后有几个
        teacher_count = (
            Classroom.objects.filter(enrollments__student=user)
            .exclude(teachings__teacher=None)
            .values("teachings__teacher")
            .distinct()
            .count()
        )

        # 我所有班里的同学，去重后有几个（不含自己）
        classmate_count = (
            Enrollment.objects.filter(classroom__enrollments__student=user)
            .exclude(student=user)
            .values("student")
            .distinct()
            .count()
        )

        return {
            "headline": "我的学习工作台",
            "lede": "你已选的教学班与授课教师。",
            "cards": [
                {"label": "已选教学班", "value": mine.count(), "hint": "个"},
                {"label": "授课教师", "value": teacher_count, "hint": "位"},
                {"label": "同班同学", "value": classmate_count, "hint": "不含本人"},
            ],
            "classes": classes,
            "show_counts": False,
            "show_teachers": True,
            "table_title": "我的教学班",
            "colspan": 4,
            "empty_hint": "还没有已选的教学班，请联系管理员安排选课。",
        }
