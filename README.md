# memelyAI – Smart Restaurant POS

Proyecto Django para gestionar el flujo completo de un restaurante: toma de pedidos, cocina, caja, inventario y reportes.

## Características principales

- **POS (Camarero):** crea pedidos por mesa y envía a cocina automáticamente.
- **Cocina:** monitor en tiempo real con HTMX, notificaciones y responsable del pedido.
- **Caja:** panel dedicado para cobros y emisión de tickets.
- **Inventario:** stock diario, stock restante, alertas de bajo stock y reporte CSV.
- **Menú público / Cliente:** menú visual con modo cliente.
- **Perfil de usuario:** avatar, username y rol visibles en la interfaz.
- **Tickets PDF:** diseño profesional con datos de empresa, QR opcional y nombre del mozo.
- **Roles y permisos:** acceso restringido por grupos (Cocina, Caja, Admin, etc.).
- **Tests:** unit tests con `pytest` y tests Django con `manage.py test`.

## Rutas principales

- `http://127.0.0.1:8000/login/` – Login
- `http://127.0.0.1:8000/dashboard/` – Dashboard (Admin)
- `http://127.0.0.1:8000/perfil/` – Perfil de usuario (avatar)
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

## Responsable del pedido

- Cada `Order` guarda el usuario que creó el pedido (`created_by`).
- En cocina se muestra el **responsable** del pedido.
- En el ticket PDF se imprime el **nombre del mozo**.

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
- Mozo a cargo (si existe)

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

## Tests

### Pytest
```
uv run pytest
```

### Django test runner
```
uv run python manage.py test
```

## Migraciones

Cada vez que agregues campos o modelos:
```
uv run python manage.py makemigrations
uv run python manage.py migrate
```

Si hay conflictos de migración (branches), ejecuta:
```
uv run python manage.py makemigrations --merge
```

Si `uv` falla:
```
C:\Tu_ruta\.venv\Scripts\python.exe manage.py makemigrations
C:\Tu_ruta\.venv\Scripts\python.exe manage.py migrate
```

## Permisos

- POS requiere permiso `orders.add_order`
- Cocina/Caja requieren `orders.view_order` y `orders.change_order` según el flujo
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
- Dashboard
  - `docs/screenshots/dashboard.png`
- Perfil
  - `docs/screenshots/perfil.png`

## Roadmap

- Roles y permisos avanzados (auditoría por usuario)
- Panel de reportes diarios / mensuales
- Exportación a Excel (XLSX)
- WebSockets para actualizaciones en tiempo real
- Módulo de reservas
- Interfaz de cliente con pagos (dark kitchen)

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
