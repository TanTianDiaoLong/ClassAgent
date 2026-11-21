"""core 应用自己的路由表。

为什么不把这几行直接写在 ClassAgent/urls.py 里？
因为项目一大，所有 app 的 URL 都堆在总表里会很难维护。
Django 的推荐做法是：每个 app 管自己的 urls.py，
总表里用 include() 把这一份"挂"上去。

app_name 的作用是给这组 URL 起个命名空间，
模板里就能写 {% url 'core:home' %}，避免和其他 app 重名。
"""

from django.urls import path

from .views import DashboardView, HomeView

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),            # -> /
    path("dashboard/", DashboardView.as_view(), name="dashboard"),  # -> /dashboard/
]
