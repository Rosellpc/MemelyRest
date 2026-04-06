from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import qr
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing

from apps.inventory.models import Category, MenuItem
from .models import Order, OrderItem, Table


def _not_in_groups(*group_names):
    def check(user):
        if user.is_superuser:
            return True
        return not user.groups.filter(name__in=group_names).exists()

    return check


@login_required  # Obliga a estar logueado
@permission_required(
    "orders.add_order", raise_exception=True
)  # Obliga a tener permiso de crear pedidos
def toma_de_pedidos(request):
    categories = Category.objects.prefetch_related("items").all()
    tables = Table.objects.order_by("number")

    if request.method == "POST":
        table_id = request.POST.get("table")
        if not table_id:
            return render(
                request,
                "orders/pos.html",
                {
                    "categories": categories,
                    "tables": tables,
                    "error": "Selecciona una mesa.",
                },
            )

        table = get_object_or_404(Table, id=table_id)
        if table.is_occupied:
            return render(
                request,
                "orders/pos.html",
                {
                    "categories": categories,
                    "tables": tables,
                    "error": "Esta mesa ya esta ocupada.",
                },
            )
        selected_items = []
        for key, value in request.POST.items():
            if not key.startswith("item_"):
                continue
            try:
                menu_id = int(key.split("_", 1)[1])
                qty = int(value)
            except (ValueError, IndexError):
                continue
            if qty > 0:
                selected_items.append((menu_id, qty))

        if not selected_items:
            return render(
                request,
                "orders/pos.html",
                {
                    "categories": categories,
                    "tables": tables,
                    "error": "Agrega al menos un plato.",
                },
            )

        menu_items = {
            m.id: m
            for m in MenuItem.objects.filter(
                id__in=[item_id for item_id, _ in selected_items],
                is_available=True,
            )
        }

        if len(menu_items) != len(selected_items):
            return render(
                request,
                "orders/pos.html",
                {
                    "categories": categories,
                    "tables": tables,
                    "error": "Hay platos no disponibles. Revisa el pedido.",
                },
            )

        try:
            with transaction.atomic():
                order = Order.objects.create(
                    table=table, status=Order.STATUS_PREPARING
                )
                table.is_occupied = True
                table.save()
                for menu_id, qty in selected_items:
                    OrderItem.objects.create(
                        order=order, menu_item=menu_items[menu_id], quantity=qty
                    )
        except ValidationError as exc:
            return render(
                request,
                "orders/pos.html",
                {
                    "categories": categories,
                    "tables": tables,
                    "error": "Stock insuficiente para uno o mas platos.",
                },
            )

        return render(
            request,
            "orders/pos.html",
            {
                "categories": categories,
                "tables": tables,
                "success": f"Pedido #{order.id} enviado a cocina.",
                "order_id": order.id,
            },
        )

    return render(
        request,
        "orders/pos.html",
        {"categories": categories, "tables": tables},
    )


@login_required
@user_passes_test(_not_in_groups("WAITER", "CUSTOMER"), login_url=None)
@permission_required("orders.view_order", raise_exception=True)
def monitor_cocina(request):
    pedidos_activos = _pedidos_activos()
    return render(request, "orders/cocina.html", {"pedidos": pedidos_activos})


@login_required
@user_passes_test(_not_in_groups("WAITER", "CUSTOMER"), login_url=None)
@permission_required("orders.view_order", raise_exception=True)
def lista_pedidos_fragmento(request):
    # Esta vista solo devuelve el pedazo de HTML de la lista
    pedidos = _pedidos_activos()
    return render(request, "orders/partials/lista_pedidos.html", {"pedidos": pedidos})


@login_required
@user_passes_test(_not_in_groups("WAITER", "CUSTOMER"), login_url=None)
@permission_required("orders.change_order", raise_exception=True)
@require_POST
def actualizar_estado_pedido(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get("status")
    payment_method = request.POST.get("payment_method")

    allowed = {
        Order.STATUS_PENDING: [Order.STATUS_PREPARING, Order.STATUS_CANCELLED],
        Order.STATUS_PREPARING: [Order.STATUS_DELIVERED, Order.STATUS_CANCELLED],
        Order.STATUS_DELIVERED: [Order.STATUS_PAID, Order.STATUS_CANCELLED],
        Order.STATUS_PAID: [],
        Order.STATUS_CANCELLED: [],
    }

    if new_status not in allowed.get(order.status, []):
        return HttpResponseBadRequest("Transicion de estado no permitida.")

    if new_status == Order.STATUS_PAID:
        if payment_method not in (Order.PAYMENT_CASH, Order.PAYMENT_CARD):
            return HttpResponseBadRequest("Metodo de pago invalido.")
        order.payment_method = payment_method
        order.paid_at = timezone.now()

    order.status = new_status
    order.save()

    if new_status in (Order.STATUS_PAID, Order.STATUS_CANCELLED) and order.table_id:
        order.table.is_occupied = False
        order.table.save()

    if request.headers.get("HX-Target") == "lista-caja":
        return render(
            request, "orders/partials/lista_caja.html", {"pedidos": _pedidos_caja()}
        )

    pedidos = _pedidos_activos()
    return render(request, "orders/partials/lista_pedidos.html", {"pedidos": pedidos})




@login_required
@user_passes_test(_not_in_groups("WAITER", "CUSTOMER"), login_url=None)
@permission_required("orders.view_order", raise_exception=True)
def caja(request):
    pedidos = _pedidos_caja()
    return render(request, "orders/caja.html", {"pedidos": pedidos})


@login_required
@user_passes_test(_not_in_groups("WAITER", "CUSTOMER"), login_url=None)
@permission_required("orders.view_order", raise_exception=True)
def lista_caja_fragmento(request):
    pedidos = _pedidos_caja()
    return render(request, "orders/partials/lista_caja.html", {"pedidos": pedidos})


@login_required
@user_passes_test(_not_in_groups("WAITER", "CUSTOMER"), login_url=None)
@permission_required("orders.view_order", raise_exception=True)
def generar_ticket_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Creamos la respuesta con el tipo de contenido PDF
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="ticket_{order.id}.pdf"'

    # Dibujamos el PDF
    p = canvas.Canvas(response)
    left = 70
    right = 520
    y = 800

    # Logo (opcional)
    try:
        logo_path = settings.COMPANY_LOGO_PATH
        if logo_path and logo_path.exists():
            p.drawImage(str(logo_path), left, y - 10, width=50, height=50, mask="auto")
    except Exception:
        pass

    p.setFont("Helvetica-Bold", 20)
    p.drawString(left + 60, y, settings.COMPANY_NAME)
    p.setFont("Helvetica", 10)
    p.drawString(left + 60, y - 14, settings.COMPANY_TAGLINE)
    p.drawRightString(right, y, "TICKET")

    y -= 40
    p.setFont("Helvetica", 10)
    p.drawString(left, y, settings.COMPANY_NIT)
    p.drawRightString(right, y, settings.COMPANY_PHONE)
    y -= 14
    p.drawString(left, y, settings.COMPANY_ADDRESS)
    p.drawRightString(right, y, f"Fecha: {order.created_at.strftime('%d/%m/%Y %H:%M')}")

    y -= 18
    p.setFont("Helvetica", 11)
    p.drawString(left, y, f"Pedido #: {order.id}")
    mesa = order.table.number if order.table_id else "-"
    p.drawRightString(right, y, f"Mesa: {mesa} | Estado: {order.get_status_display()}")

    y -= 18
    p.line(left, y, right, y)
    y -= 16

    p.setFont("Helvetica-Bold", 11)
    p.drawString(left, y, "Item")
    p.drawRightString(right, y, "Importe")
    y -= 12
    p.setFont("Helvetica", 11)
    p.line(left, y, right, y)

    y -= 18
    for item in order.items.all():
        item_name = f"{item.quantity} x {item.menu_item.name}"
        p.drawString(left, y, item_name)
        p.drawRightString(right, y, f"${item.price_at_order * item.quantity}")
        y -= 16
        if y < 120:
            p.showPage()
            y = 800
            p.setFont("Helvetica-Bold", 11)
            p.drawString(left, y, "Item")
            p.drawRightString(right, y, "Importe")
            y -= 12
            p.setFont("Helvetica", 11)
            p.line(left, y, right, y)
            y -= 18

    y -= 4
    p.line(left, y, right, y)
    y -= 20
    p.setFont("Helvetica-Bold", 13)
    p.drawString(left, y, "TOTAL A PAGAR")
    p.drawRightString(right, y, f"${order.total_amount}")

    y -= 20
    p.setFont("Helvetica", 10)
    if order.payment_method:
        p.drawString(left, y, f"Metodo de pago: {order.get_payment_method_display()}")
        if order.paid_at:
            p.drawRightString(right, y, f"Pagado: {order.paid_at.strftime('%d/%m/%Y %H:%M')}")
    else:
        p.drawString(left, y, "Metodo de pago: Pendiente")

    y -= 24
    p.line(left, y, right, y)
    y -= 14
    p.setFont("Helvetica", 9)
    p.drawString(left, y, settings.COMPANY_RETURN_POLICY)

    # QR (opcional)
    try:
        qr_value = f"memelyAI|pedido:{order.id}|total:{order.total_amount}"
        widget = qr.QrCodeWidget(qr_value)
        bounds = widget.getBounds()
        size = 70
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        d = Drawing(size, size)
        d.add(widget)
        renderPDF.draw(d, p, right - size, 90)
    except Exception:
        pass

    p.showPage()
    p.save()
    return response


def _pedidos_activos():
    return (
        Order.objects.filter(
            status__in=[
                Order.STATUS_PENDING,
                Order.STATUS_PREPARING,
                Order.STATUS_DELIVERED,
            ]
        )
        .select_related("table")
        .prefetch_related("items", "items__menu_item")
        .order_by("created_at")
    )


def _pedidos_caja():
    return (
        Order.objects.filter(status=Order.STATUS_DELIVERED)
        .select_related("table")
        .prefetch_related("items", "items__menu_item")
        .order_by("created_at")
    )
