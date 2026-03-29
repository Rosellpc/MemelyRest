from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Order, OrderItem, Table

admin.site.register(Table)
admin.site.register(OrderItem)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # Cuántos espacios vacíos mostrar para agregar platos
    readonly_fields = ("price_at_order",)  # El camarero no debe tocar el precio


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "table",
        "status",
        "total_amount",
        "created_at",
        "descargar_ticket",
    )
    list_filter = ("status", "table")
    inlines = [OrderItemInline]  # Aquí metemos los platos dentro del pedido
    readonly_fields = ("total_amount",)  # El total se calcula solo, no se edita manual

    def descargar_ticket(self, obj):
        if obj.id:
            url = reverse("generar_ticket", args=[obj.id])
            return format_html('<a class="button" href="{}">📄 PDF</a>', url)
        return ""

    descargar_ticket.short_description = "Ticket"
