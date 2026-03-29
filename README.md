# memelyAI – Smart Restaurant POS

Proyecto Django para gestionar el flujo completo de un restaurante: toma de pedidos, cocina, caja, inventario y reportes.

## Características principales

- **POS (Camarero):** crea pedidos por mesa y envía a cocina automáticamente.
- **Cocina:** monitor en tiempo real con HTMX, notificaciones y control de stock diario.
- **Caja:** panel dedicado para cobros y emisión de tickets.
- **Inventario:** stock diario, stock restante, alertas de bajo stock y reporte CSV.
- **Tickets PDF:** diseño profesional con datos de empresa y QR opcional.
- **Roles y permisos:** acceso restringido por grupos (Cocina, Admins, etc.).
- **Tests:** unit tests con pytest + pytest-django.

## Rutas principales

- `http://127.0.0.1:8000/login/` – Login
- `http://127.0.0.1:8000/pos/` – Toma de pedidos (camarero)
- `http://127.0.0.1:8000/cocina/` – Monitor de cocina
- `http://127.0.0.1:8000/caja/` – Caja (cobros)
- `http://127.0.0.1:8000/cocina/stock/` – Stock diario (solo cocina/admin)
- `http://127.0.0.1:8000/menu/` – Menú público

## Flujo de estados

1. **POS crea pedido** → `PREPARING`
2. **Cocina envía a caja** → `DELIVERED`
3. **Caja cobra** → `PAID`
4. **Cancelación** en cualquier etapa activa → `CANCELLED`

## Inventario y stock

- Cada `MenuItem` tiene `stock` y `low_stock_threshold`.
- Al crear un pedido se descuenta stock automáticamente.
- Cuando stock llega a 0, el plato queda **No disponible**.
- En `cocina/stock/` puedes:
  - Ver **cantidad actual**
  - Ingresar **stock nuevo** (se suma)
  - Confirmar **stock final del turno**
  - Descargar **reporte CSV**

## Reportes

Desde `cocina/stock/` puedes descargar un CSV con:
- Categoría
- Plato
- Cantidad vendida
- Total de ventas
- Stock actual
- Total general de ventas

## Tickets PDF

El ticket incluye:
- Nombre empresa (memelyAI)
- NIT, dirección, teléfono
- Estado del pedido
- Total y método de pago
- Política de devolución
- QR opcional

Configurable en `MyWeb/settings.py`:
```
COMPANY_NAME
COMPANY_TAGLINE
COMPANY_NIT
COMPANY_ADDRESS
COMPANY_PHONE
COMPANY_RETURN_POLICY
COMPANY_LOGO_PATH
```

Para incluir logo, coloca el archivo en:
```
media/logo.png
```

## Tests con pytest

Instalado:
- `pytest`
- `pytest-django`

Ejecutar tests:
```
uv run pytest
```

## Migraciones

Cada vez que agregues campos o modelos:
```
uv run python manage.py makemigrations
uv run python manage.py migrate
```

Si `uv` falla:
```
C:\Tu_ruta\.venv\Scripts\python.exe manage.py makemigrations
C:\Tu_ruta\.venv\Scripts\python.exe manage.py migrate
```

## Permisos

- POS requiere permiso `orders.add_order`
- Stock diario requiere grupo **Cocina**, **Admins** o superusuario

## Requisitos

- Python 3.13+
- Django 6.0.3
- Pillow
- ReportLab

---

memelyAI – Smart Kitchen & POS

## Capturas de pantalla

Agrega imágenes en `docs/screenshots/` y enlázalas aquí:

- POS
  - `docs/screenshots/pos.png`
- Cocina
  - `docs/screenshots/cocina.png`
- Caja
  - `docs/screenshots/caja.png`
- Stock
  - `docs/screenshots/stock.png`

## Roadmap

- Roles y permisos avanzados (auditoría por usuario)
- Panel de reportes diarios / mensuales
- Exportación a Excel (XLSX)
- WebSockets para actualizaciones en tiempo real
- Módulo de reservas

## Tabla de features por rol

| Rol      | POS | Cocina | Caja | Stock Diario | Reportes | Admin |
|----------|-----|--------|------|--------------|----------|-------|
| Mesero   |  ✅ |   ❌   |  ❌  |      ❌      |    ❌    |   ❌  |
| Cocina   |  ❌ |   ✅   |  ❌  |      ✅      |    ✅    |   ❌  |
| Caja     |  ❌ |   ❌   |  ✅  |      ❌      |    ✅    |   ❌  |
| Admin    |  ✅ |   ✅   |  ✅  |      ✅      |    ✅    |   ✅  |

## Variables de entorno

Copia el archivo `.env.example` y crea tu propio `.env`:

```
DJANGO_SECRET_KEY=change-me
```

El archivo `.env` no se sube a GitHub.
