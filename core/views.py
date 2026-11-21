"""core 应用：放全站公共页面。

这个文件里只有两个视图：

    HomeView      ->  /             欢迎页，谁都能看
    DashboardView ->  /dashboard/   仪表盘，必须登录才能看

两个视图都要做同一件事：先判断"当前这个人是什么角色"，
再决定给他看什么数据。所以判断逻辑被抽成了下面的 audience_of()。
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import render
from django.views import View

from classroom.models import ClassRoom, Enrollment
from user.models import User
from user.models.enum import UserRole


# ---------------------------------------------------------------------------
# 一、公共的小工具
# ---------------------------------------------------------------------------

def audience_of(user) -> str:
    """判断当前用户属于哪种视角，返回 "guest" / "admin" / "teacher" / "student"。

    user.is_admin() 这类方法是 user/models/user.py 里定义的，
    核心就是判断 role 字段（外加 is_superuser）。
    """
    if not user.is_authenticated:
        return "guest"
    if user.is_admin():
        return "admin"
    if user.is_teacher():
        return "teacher"
    return "student"


ROLE_LABEL = {
    "guest": "访客",
    "admin": "管理员",
    "teacher": "教师",
    "student": "学生",
}

# 欢迎页上的三张"能力卡片"，按角色不一样。
# 之所以用字典放在模块顶层，是因为它是静态文案，不依赖数据库，
# 每次请求都重新构造纯属浪费。
CAPABILITIES = {
    "admin": [
        ("01 / ADMIN", "教学班配置", "创建教学班，维护编号、科目与学期。"),
        ("02 / MEMBERS", "成员与角色", "管理教师、学生账号以及角色分配。"),
        ("03 / BINDING", "任课与选课", "绑定任课教师，维护学生选课关系。"),
    ],
    "teacher": [
        ("01 / TEACHING", "我的教学班", "查看任教班级、学生名单与班级规模。"),
        ("02 / STUDENTS", "学生名单", "按教学班查看已选课的学生。"),
        ("03 / COURSE", "课程信息", "核对科目、学期与班级编号。"),
    ],
    "student": [
        ("01 / CLASSES", "我的课程", "查看已选教学班与所在学期。"),
        ("02 / TEACHERS", "授课教师", "查看每门课程的任课教师。"),
        ("03 / PROFILE", "个人账号", "核对学号、邮箱与账号状态。"),
    ],
}

WELCOME_LEDE = {
    "admin": "你有系统管理权限，可以维护教学班、成员与全部绑定关系。",
    "teacher": "工作台会汇总你任教的教学班与学生规模，从这里开始今天的工作。",
    "student": "工作台会汇总你已选的教学班与授课教师，从这里开始今天的学习。",
}


# ---------------------------------------------------------------------------
# 二、首页（欢迎页）
# ---------------------------------------------------------------------------

class HomeView(View):
    """访问 / 时执行。

    GET 请求才会走 get()；POST 会返回 405，这对欢迎页来说正好。
    """

    template_name = "index.html"

    def get(self, request):
        audience:str = audience_of(request.user)

        context = {
            "audience": audience,
            "role_label": ROLE_LABEL[audience],
        }

        # 游客：只给静态介绍，不碰数据库。
        if audience == "guest":
            context["page_title"] = "ClassAgent · 班级智能协作系统"
            return render(request, self.template_name, context)

        # 已登录：加欢迎语和角色能力卡。
        name = request.user.display_name()
        context.update(
            page_title=f"欢迎，{name} · ClassAgent",
            display_name=name,
            headline=f"{name}，欢迎回来。",
            lede=WELCOME_LEDE[audience],
            capabilities=CAPABILITIES[audience],
        )
        return render(request, self.template_name, context)


# ---------------------------------------------------------------------------
# 三、仪表盘
# ---------------------------------------------------------------------------

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
            ClassRoom.objects.prefetch_related("teachings__teacher")
            .annotate(student_count=Count("enrollments"))
            .order_by("serial")
        )
        return {
            "headline": "系统总览",
            "lede": "教学班、成员与选课关系的最新汇总。",
            "cards": [
                {"label": "教学班", "value": ClassRoom.objects.count(), "hint": "全部"},
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
        mine = ClassRoom.objects.filter(teachings__teacher=user)
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
            ClassRoom.objects.filter(enrollments__student=user)
            .prefetch_related("teachings__teacher")
            .order_by("serial")
        )

        # 我所有班里的老师，去重后有几个
        teacher_count = (
            ClassRoom.objects.filter(enrollments__student=user)
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
