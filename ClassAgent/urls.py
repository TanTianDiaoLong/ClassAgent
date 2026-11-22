"""
URL configuration for ClassAgent project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from user.views import LoginView, LogoutView
urlpatterns = [
    path('login/', view=LoginView.as_view(), name='login'),
    path('logout/', view=LogoutView.as_view(), name='logout'),

    path("api/v1/", include("api.urls")),

    # 后台管理必须写在 include 之前：core 的路径是空字符串 ''，
    # 如果它排在前面，/admin/ 会被 core 先接走然后 404。
    path("admin/", admin.site.urls), # TODO: Will remove in future.

    # 首页（/）和仪表盘（/dashboard/）交给 core 应用自己管
    path('', include('core.urls')),
]
