from django.urls import path

from .views import menu_digital

urlpatterns = [
    path("menu/", menu_digital, name="menu_digital"),
]
