from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.inventory.models import Category, MenuItem, StockAdjustment
from apps.orders.models import Order, OrderItem, Table


class InventoryStockTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="cocina", password="testpass123"
        )
        cocina_group, _ = Group.objects.get_or_create(name="Cocina")
        self.user.groups.add(cocina_group)
        self.category = Category.objects.create(name="Postres")
        self.item = MenuItem.objects.create(
            category=self.category,
            name="Cheesecake",
            description="Clasico",
            price=12,
            is_available=True,
            stock=5,
        )

    def test_add_stock_action_adds_quantity(self):
        self.client.force_login(self.user)
        url = reverse("stock_diario_cocina")
        response = self.client.post(
            url,
            {"action": "add_stock", f"new_stock_{self.item.id}": "3"},
        )
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.stock, 8)
        self.assertTrue(StockAdjustment.objects.filter(menu_item=self.item).exists())

    def test_reporte_ventas_csv_includes_total(self):
        self.client.force_login(self.user)
        table = Table.objects.create(number=10)
        order = Order.objects.create(table=table)
        OrderItem.objects.create(order=order, menu_item=self.item, quantity=2)

        url = reverse("reporte_ventas_csv")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("TOTAL VENTAS", content)
        self.assertIn("Cheesecake", content)


class StockDecrementTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Bebidas")
        self.item = MenuItem.objects.create(
            category=self.category,
            name="Limonada",
            description="Fresca",
            price=10,
            is_available=True,
            stock=5,
        )
        self.table = Table.objects.create(number=1)
        self.order = Order.objects.create(table=self.table)

    def test_order_item_decrements_stock(self):
        OrderItem.objects.create(order=self.order, menu_item=self.item, quantity=2)
        self.item.refresh_from_db()
        self.assertEqual(self.item.stock, 3)
