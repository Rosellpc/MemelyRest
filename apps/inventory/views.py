import csv

from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.db import transaction
from django.http import HttpResponse
from django.db.models import F, Sum
from django.shortcuts import render
from django.core.exceptions import PermissionDenied

from .models import Category, MenuItem, StockAdjustment
from apps.orders.models import OrderItem


def menu_digital(request):
    # Traemos las categorías que tienen platos disponibles
    categories = Category.objects.prefetch_related("items").all()
    return render(request, "inventory/menu.html", {"categories": categories})



def _can_manage_stock(user):
    if user.is_superuser:
        return True
    if user.groups.filter(name__iexact="Admins").exists():
        return True
    if user.groups.filter(name__iexact="Cocina").exists():
        return True
    if user.groups.filter(name__iexact="COCINA").exists():
        return True
    return user.has_perm("inventory.change_menuitem")


@login_required
@user_passes_test(_can_manage_stock, login_url=None)
def stock_diario(request):
    items = list(
        MenuItem.objects.select_related("category").order_by("category__name", "name")
    )
    history = StockAdjustment.objects.select_related("menu_item", "user")[:30]

    if request.method == "POST":
        action = request.POST.get("action")
        warning = None
        error = None
        with transaction.atomic():
            if action == "add_stock":
                any_added = False
                negative_found = False
                for item in items:
                    previous = item.stock
                    value = request.POST.get(f"new_stock_{item.id}")
                    try:
                        add_qty = int(value) if value is not None else 0
                    except ValueError:
                        add_qty = 0

                    if add_qty < 0:
                        negative_found = True
                    add_qty = max(0, add_qty)
                    if add_qty > 0:
                        any_added = True
                        item.stock = previous + add_qty
                        item.is_available = item.stock > 0
                        item.save(update_fields=["stock", "is_available"])
                        StockAdjustment.objects.create(
                            menu_item=item,
                            user=request.user,
                            previous_stock=previous,
                            new_stock=item.stock,
                        )

                if negative_found:
                    error = "No se permiten valores negativos."
                if not any_added and not error:
                    warning = "No ingresaste stock nuevo en ningun plato."

            elif action == "carryover":
                for item in items:
                    # Solo confirmamos el stock actual al cierre del turno
                    is_available = item.stock > 0
                    if item.is_available != is_available:
                        item.is_available = is_available
                        item.save(update_fields=["is_available"])

        history = StockAdjustment.objects.select_related("menu_item", "user")[:30]
        message = (
            "Stock actualizado con ingreso nuevo."
            if action == "add_stock"
            else "Stock final del turno actualizado."
        )
        ctx = {"items": items, "history": history}
        if error:
            ctx["error"] = error
        elif warning:
            ctx["warning"] = warning
        else:
            ctx["success"] = message
        return render(request, "inventory/stock.html", ctx)

    return render(
        request,
        "inventory/stock.html",
        {"items": items, "history": history},
    )


@login_required
@user_passes_test(_can_manage_stock, login_url=None)
def reporte_ventas_csv(request):
    items = (
        MenuItem.objects.select_related("category")
        .all()
        .order_by("category__name", "name")
    )

    ventas = {}
    for row in (
        OrderItem.objects.values("menu_item_id")
        .annotate(
            total_qty=Sum("quantity"),
            total_revenue=Sum(F("quantity") * F("price_at_order")),
        )
        .all()
    ):
        ventas[row["menu_item_id"]] = row

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="reporte_ventas.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "Categoria",
            "Plato",
            "Cantidad Vendida",
            "Total Ventas",
            "Stock Actual",
        ]
    )

    for item in items:
        data = ventas.get(item.id, {})
        qty = data.get("total_qty") or 0
        total = data.get("total_revenue") or 0
        writer.writerow([item.category.name, item.name, qty, total, item.stock])

    # Total general
    total_general = sum(
        (row.get("total_revenue") or 0) for row in ventas.values()
    )
    writer.writerow([])
    writer.writerow(["TOTAL VENTAS", "", "", total_general, ""])

    return response
