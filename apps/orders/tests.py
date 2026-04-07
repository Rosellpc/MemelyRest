from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.inventory.models import Category, MenuItem
from .models import Order, OrderItem, Table


class OrderItemModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Bebidas")
        self.menu_item = MenuItem.objects.create(
            category=self.category,
            name="Limonada",
            description="Fresca",
            price=10,
            is_available=True,
            stock=10,
        )
        self.table = Table.objects.create(number=1)
        self.order = Order.objects.create(table=self.table)

    def test_order_item_updates_order_total(self):
        OrderItem.objects.create(order=self.order, menu_item=self.menu_item, quantity=2)
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_amount, 20)

    def test_order_item_rejects_invalid_quantity(self):
        item = OrderItem(order=self.order, menu_item=self.menu_item, quantity=0)
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_order_item_rejects_unavailable_menu_item(self):
        self.menu_item.is_available = False
        self.menu_item.save()
        item = OrderItem(order=self.order, menu_item=self.menu_item, quantity=1)
        with self.assertRaises(ValidationError):
            item.full_clean()


class CocinaViewsTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Entradas")
        self.menu_item = MenuItem.objects.create(
            category=self.category,
            name="Arepa",
            description="Con queso",
            price=5,
            is_available=True,
            stock=10,
        )
        self.table = Table.objects.create(number=2)
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="cocina_test", password="pass123"
        )
        cocina_group, _ = Group.objects.get_or_create(name="COCINA")
        self.user.groups.add(cocina_group)
        perm = Permission.objects.get(codename="view_order")
        self.user.user_permissions.add(perm)
        self.client.force_login(self.user)

    def test_monitor_cocina_returns_200(self):
        url = reverse("monitor_cocina")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_lista_pedidos_fragmento_filters_status(self):
        pending = Order.objects.create(table=self.table, status="PENDING")
        delivered = Order.objects.create(table=self.table, status="DELIVERED")
        url = reverse("lista_pedidos_fragmento")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"#{pending.id}")
        self.assertContains(response, f"#{delivered.id}")
