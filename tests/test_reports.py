import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from apps.inventory.models import Category, MenuItem
from apps.orders.models import Order, OrderItem, Table


@pytest.mark.django_db
def test_sales_report_csv_totals(client, django_user_model):
    user = django_user_model.objects.create_user(username="cocina2", password="pass123")
    cocina_group, _ = Group.objects.get_or_create(name="COCINA")
    user.groups.add(cocina_group)
    client.force_login(user)

    category = Category.objects.create(name="Postres")
    item = MenuItem.objects.create(
        category=category,
        name="Tiramisu",
        description="Clasico",
        price=15,
        is_available=True,
        stock=10,
    )
    table = Table.objects.create(number=2)
    order = Order.objects.create(table=table)
    OrderItem.objects.create(order=order, menu_item=item, quantity=3)

    url = reverse("reporte_ventas_csv")
    resp = client.get(url)
    assert resp.status_code == 200
    content = resp.content.decode("utf-8")
    assert "Tiramisu" in content
    assert "TOTAL VENTAS" in content


@pytest.mark.django_db
def test_stock_addition_sums_correctly(client, django_user_model):
    user = django_user_model.objects.create_user(username="cocina3", password="pass123")
    cocina_group, _ = Group.objects.get_or_create(name="COCINA")
    user.groups.add(cocina_group)
    client.force_login(user)

    category = Category.objects.create(name="Bebidas")
    item = MenuItem.objects.create(
        category=category,
        name="Te frio",
        description="Limon",
        price=8,
        is_available=True,
        stock=4,
    )

    url = reverse("stock_diario_cocina")
    resp = client.post(
        url,
        {"action": "add_stock", f"new_stock_{item.id}": "6"},
    )
    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.stock == 10


@pytest.mark.django_db
def test_login_and_permissions(client, django_user_model):
    user = django_user_model.objects.create_user(username="waiter2", password="pass123")
    waiter_group, _ = Group.objects.get_or_create(name="WAITER")
    user.groups.add(waiter_group)
    perm = Permission.objects.get(codename="add_order")
    user.user_permissions.add(perm)

    client.force_login(user)
    resp = client.get(reverse("toma_de_pedidos"))
    assert resp.status_code == 200

    # Waiter no debe acceder a cocina ni caja
    resp2 = client.get(reverse("monitor_cocina"))
    assert resp2.status_code in (302, 403)
    resp3 = client.get(reverse("caja"))
    assert resp3.status_code in (302, 403)



@pytest.mark.django_db
def test_customer_menu_access(client, django_user_model):
    user = django_user_model.objects.create_user(username="cliente1", password="pass123")
    customer_group, _ = Group.objects.get_or_create(name="CUSTOMER")
    user.groups.add(customer_group)

    # Dar permiso de ver menu
    perm = Permission.objects.get(codename="view_menuitem")
    user.user_permissions.add(perm)

    client.force_login(user)
    resp = client.get(reverse("menu_digital"))
    assert resp.status_code == 200
    resp2 = client.get(reverse("toma_de_pedidos"))
    assert resp2.status_code in (302, 403)
    resp3 = client.get(reverse("monitor_cocina"))
    assert resp3.status_code in (302, 403)
    resp4 = client.get(reverse("caja"))
    assert resp4.status_code in (302, 403)


@pytest.mark.django_db
def test_role_login_redirects(client, django_user_model):
    waiter = django_user_model.objects.create_user(username="waiter_login", password="pass123")
    waiter_group, _ = Group.objects.get_or_create(name="WAITER")
    waiter.groups.add(waiter_group)

    resp = client.post("/login/", {"username": "waiter_login", "password": "pass123"})
    assert resp.status_code == 302
    assert resp.url == "/pos/"



@pytest.mark.django_db
def test_dashboard_requires_admin(client, django_user_model):
    user = django_user_model.objects.create_user(username="normal", password="pass123")
    client.force_login(user)
    resp = client.get("/dashboard/")
    assert resp.status_code in (302, 403)

    admin = django_user_model.objects.create_superuser(username="admin_dash", password="pass123")
    client.force_login(admin)
    resp2 = client.get("/dashboard/")
    assert resp2.status_code == 200


@pytest.mark.django_db
def test_register_page_available(client):
    resp = client.get("/register/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_caja_permissions(client, django_user_model):
    user = django_user_model.objects.create_user(username="caja_user", password="pass123")
    caja_group, _ = Group.objects.get_or_create(name="CAJA")
    user.groups.add(caja_group)
    perm = Permission.objects.get(codename="view_order")
    user.user_permissions.add(perm)

    client.force_login(user)
    resp = client.get(reverse("caja"))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_cocina_permissions(client, django_user_model):
    user = django_user_model.objects.create_user(username="cocina_user", password="pass123")
    cocina_group, _ = Group.objects.get_or_create(name="COCINA")
    user.groups.add(cocina_group)
    perm = Permission.objects.get(codename="view_order")
    user.user_permissions.add(perm)

    client.force_login(user)
    resp = client.get(reverse("monitor_cocina"))
    assert resp.status_code == 200



@pytest.mark.django_db
def test_role_redirects_for_each_group(client, django_user_model):
    roles = {
        "WAITER": "/pos/",
        "COCINA": "/cocina/",
        "CAJA": "/caja/",
        "CUSTOMER": "/menu/",
    }
    for role, url in roles.items():
        user = django_user_model.objects.create_user(
            username=f"user_{role}", password="pass123"
        )
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)

        resp = client.post("/login/", {"username": user.username, "password": "pass123"})
        assert resp.status_code == 302
        assert resp.url == url


@pytest.mark.django_db
def test_logout_redirects_to_login(client, django_user_model):
    user = django_user_model.objects.create_user(username="logout_user", password="pass123")
    client.force_login(user)
    resp = client.get("/logout/")
    assert resp.status_code == 302
    assert resp.url == "/login/"
