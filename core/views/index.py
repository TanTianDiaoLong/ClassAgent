from django.views import View
from django.shortcuts import render

from .utils import audience_of, ROLE_LABEL, WELCOME_LEDE, CAPABILITIES

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