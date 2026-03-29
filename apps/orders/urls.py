from django.urls import path

from . import views
from apps.inventory.views import reporte_ventas_csv, stock_diario
from .views import generar_ticket_pdf

urlpatterns = [
    path("ticket/<int:order_id>/", generar_ticket_pdf, name="generar_ticket"),
    path("pos/", views.toma_de_pedidos, name="toma_de_pedidos"),
    path("cocina/", views.monitor_cocina, name="monitor_cocina"),
    path("cocina/stock/", stock_diario, name="stock_diario_cocina"),
    path("cocina/stock/reporte.csv", reporte_ventas_csv, name="reporte_ventas_csv"),
    path("caja/", views.caja, name="caja"),
    path("caja/actualizar/", views.lista_caja_fragmento, name="lista_caja_fragmento"),
    path(
        "cocina/actualizar/",
        views.lista_pedidos_fragmento,
        name="lista_pedidos_fragmento",
    ),
    path(
        "cocina/estado/<int:order_id>/",
        views.actualizar_estado_pedido,
        name="actualizar_estado_pedido",
    ),
]
