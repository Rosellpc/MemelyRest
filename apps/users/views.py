from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse
from .forms import CustomUserCreationForm


class RoleBasedLoginView(LoginView):
    template_name = "registration/login.html"

    def _has_group(self, *names):
        names = {n.lower() for n in names}
        return any(g.name.lower() in names for g in self.request.user.groups.all())

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return "/dashboard/"

        if self._has_group("admin", "admins"):
            return "/dashboard/"

        if self._has_group("waiter"):
            return "/pos/"
        if self._has_group("caja", "box"):
            return "/caja/"
        if self._has_group("cocina", "kitchen"):
            return "/cocina/"
        if self._has_group("customer", "cliente"):
            return "/menu/"

        return "/"


def role_based_logout(request):
    logout(request)
    return redirect("/login/")


def home(request):
    return render(request, "users/home.html")


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            customer_group, _ = Group.objects.get_or_create(name="CUSTOMER")
            user.groups.add(customer_group)
            messages.success(
                request, "Cuenta creada. Ya puedes iniciar sesion como Cliente."
            )
            return redirect("login")
    else:
        form = CustomUserCreationForm()

    return render(request, "users/register.html", {"form": form})



def _is_admin(user):
    return user.is_superuser


@login_required
@user_passes_test(_is_admin, login_url=None)
def admin_dashboard(request):
    return render(request, "users/admin_dashboard.html")
