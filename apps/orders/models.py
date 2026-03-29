from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Sum

from apps.inventory.models import MenuItem


class Table(models.Model):
    number = models.IntegerField(unique=True)
    is_occupied = models.BooleanField(default=False)

    def __str__(self):
        return f"Mesa {self.number}"


class Order(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_PREPARING = "PREPARING"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_PAID = "PAID"
    STATUS_CANCELLED = "CANCELLED"

    PAYMENT_CASH = "CASH"
    PAYMENT_CARD = "CARD"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_PREPARING, "En Cocina"),
        (STATUS_DELIVERED, "Entregado"),
        (STATUS_PAID, "Pagado"),
        (STATUS_CANCELLED, "Cancelado"),
    ]

    PAYMENT_CHOICES = [
        (PAYMENT_CASH, "Efectivo"),
        (PAYMENT_CARD, "Tarjeta"),
    ]

    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_method = models.CharField(
        max_length=10, choices=PAYMENT_CHOICES, blank=True, null=True
    )
    paid_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Pedido {self.id} - {self.table}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(
        max_digits=10, decimal_places=2, editable=False
    )

    def clean(self):
        errors = {}
        if self.quantity is not None and self.quantity < 1:
            errors["quantity"] = "La cantidad debe ser al menos 1."

        if self.menu_item_id:
            if not self.menu_item.is_available:
                errors["menu_item"] = "El plato no esta disponible."
            if self.menu_item.stock is not None and self.menu_item.stock < self.quantity:
                errors["quantity"] = "Stock insuficiente para este plato."
            if self.menu_item.price is not None and self.menu_item.price <= 0:
                errors["menu_item"] = "El plato debe tener un precio valido."

        if self.price_at_order is not None and self.price_at_order <= 0:
            errors["price_at_order"] = "El precio debe ser mayor a 0."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # 1. Capturamos el precio actual del plato automaticamente
        is_new = self._state.adding
        if not self.price_at_order and self.menu_item_id:
            self.price_at_order = self.menu_item.price

        self.full_clean()
        super().save(*args, **kwargs)

        if is_new and self.menu_item_id:
            self.menu_item.stock = max(0, self.menu_item.stock - self.quantity)
            if self.menu_item.stock == 0:
                self.menu_item.is_available = False
            self.menu_item.save(update_fields=["stock", "is_available"])

        # 2. Al guardar un ítem, actualizamos el total del Pedido (Order)
        total = (
            self.order.items.aggregate(total=Sum(F("quantity") * F("price_at_order")))[
                "total"
            ]
            or 0
        )
        self.order.total_amount = total
        self.order.save()

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name}"
