from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


ROLE_PERMISSIONS = {
    "WAITER": [
        "orders.view_table",
        "orders.add_order",
        "orders.change_order",
        "orders.view_order",
        "orders.add_orderitem",
        "orders.change_orderitem",
        "orders.view_orderitem",
        "inventory.view_category",
        "inventory.view_menuitem",
    ],
    "CUSTOMER": [
        "orders.view_order",
        "inventory.view_menuitem",
    ],
    "COCINA": [
        "inventory.change_menuitem",
        "inventory.view_menuitem",
        "inventory.view_category",
        "orders.view_order",
        "orders.change_order",
        "orders.view_orderitem",
    ],
    "CAJA": [
        "orders.view_order",
        "orders.change_order",
        "orders.view_orderitem",
    ],
}


class Command(BaseCommand):
    help = "Crea y actualiza grupos y permisos base del sistema."

    def handle(self, *args, **options):
        for role, perm_codes in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=role)
            perms = []
            for code in perm_codes:
                app_label, codename = code.split(".")
                try:
                    perm = Permission.objects.get(
                        content_type__app_label=app_label, codename=codename
                    )
                    perms.append(perm)
                except Permission.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Permiso no encontrado: {code}"))

            group.permissions.set(perms)
            self.stdout.write(self.style.SUCCESS(f"Grupo {role} actualizado"))

        self.stdout.write(self.style.SUCCESS("Roles configurados correctamente"))
