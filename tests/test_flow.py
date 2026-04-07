import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from apps.inventory.models import Category, MenuItem
from apps.orders.models import Order, OrderItem, Table


@pytest.mark.django_db
def test_flow_pos_cocina_caja(client, django_user_model):
    waiter = django_user_model.objects.create_user(username="mesero", password="pass123")
    waiter_group, _ = Group.objects.get_or_create(name="WAITER")
    waiter.groups.add(waiter_group)
    perm = Permission.objects.get(codename="add_order")
    waiter.user_permissions.add(perm)
    client.force_login(waiter)

    category = Category.objects.create(name="Bebidas")
    item = MenuItem.objects.create(
        category=category,
        name="Limonada",
        description="Fresca",
        price=10,
        is_available=True,
        stock=10,
    )
    table = Table.objects.create(number=1)

    url_pos = reverse("toma_de_pedidos")
    resp = client.post(url_pos, {"table": str(table.id), f"item_{item.id}": "2"})
    assert resp.status_code == 200

    order = Order.objects.latest("id")
    assert order.status == Order.STATUS_PREPARING
    assert order.created_by == waiter

    item.refresh_from_db()
    assert item.stock == 8
    table.refresh_from_db()
    assert table.is_occupied is True

    admin = django_user_model.objects.create_superuser(username="admin", password="pass123")
    client.force_login(admin)
    url_estado = reverse("actualizar_estado_pedido", args=[order.id])
    resp = client.post(url_estado, {"status": Order.STATUS_DELIVERED})
    assert resp.status_code == 200

    order.refresh_from_db()
    assert order.status == Order.STATUS_DELIVERED

    resp = client.post(
        url_estado,
        {"status": Order.STATUS_PAID, "payment_method": Order.PAYMENT_CASH},
    )
    assert resp.status_code == 200

    order.refresh_from_db()
    assert order.status == Order.STATUS_PAID
    assert order.payment_method == Order.PAYMENT_CASH
    table.refresh_from_db()
    assert table.is_occupied is False


@pytest.mark.django_db
def test_stock_permission_by_role(client, django_user_model):
    user = django_user_model.objects.create_user(username="cocina", password="pass123")
    cocina_group, _ = Group.objects.get_or_create(name="COCINA")
    user.groups.add(cocina_group)

    client.force_login(user)
    url = reverse("stock_diario_cocina")
    resp = client.get(url)
    assert resp.status_code == 200


@pytest.mark.django_db
def test_ticket_pdf_generates(client, django_user_model):
    admin = django_user_model.objects.create_superuser(username="admin2", password="pass123")
    client.force_login(admin)
    category = Category.objects.create(name="Platos")
    item = MenuItem.objects.create(
        category=category,
        name="Hamburguesa",
        description="Clasica",
        price=20,
        is_available=True,
        stock=10,
    )
    table = Table.objects.create(number=5)
    order = Order.objects.create(table=table, created_by=admin)
    OrderItem.objects.create(order=order, menu_item=item, quantity=1)

    url = reverse("generar_ticket", args=[order.id])
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"
