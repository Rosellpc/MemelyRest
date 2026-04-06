from django.urls import path

from .views import (
    RoleBasedLoginView,
    role_based_logout,
    admin_dashboard,
    home,
    register,
)

urlpatterns = [
    path("", home, name="home"),
    path("login/", RoleBasedLoginView.as_view(), name="login"),
    path("logout/", role_based_logout, name="logout"),
    path("register/", register, name="register"),
    path("dashboard/", admin_dashboard, name="admin_dashboard"),
]
