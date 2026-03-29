import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from apps.inventory.models import Category, MenuItem
from apps.orders.models import Order, OrderItem, Table


@pytest.mark.django_db
def test_sales_report_csv_totals(client, django_user_model):
    user = django_user_model.objects.create_user(username="cocina2", password="pass123")
    cocina_group, _ = Group.objects.get_or_create(name="Cocina")
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
    cocina_group, _ = Group.objects.get_or_create(name="Cocina")
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
    user = django_user_model.objects.create_user(username="mesero2", password="pass123")
    perm = Permission.objects.get(codename="add_order")
    user.user_permissions.add(perm)

    client.force_login(user)
    resp = client.get(reverse("toma_de_pedidos"))
    assert resp.status_code == 200

    # Sin grupo cocina no debe acceder a stock
    resp2 = client.get(reverse("stock_diario_cocina"))
    assert resp2.status_code in (302, 403)
