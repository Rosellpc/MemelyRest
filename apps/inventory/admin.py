from django.contrib import admin

from .models import Category, MenuItem, StockAdjustment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "is_available", "low_stock")
    list_filter = ("category", "is_available")  # Filtros laterales
    search_fields = ("name",)  # Buscador

    def low_stock(self, obj):
        return obj.is_low_stock

    low_stock.boolean = True
    low_stock.short_description = "Stock bajo"


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ("menu_item", "previous_stock", "new_stock", "user", "created_at")
    list_filter = ("created_at", "menu_item")
    search_fields = ("menu_item__name", "user__username")

    def has_module_permission(self, request):
        # Si es superusuario ve todo, si no, solo si tiene permiso específico
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name="Admins").exists()
