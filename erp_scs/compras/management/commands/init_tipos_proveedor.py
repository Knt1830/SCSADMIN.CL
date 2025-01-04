# compras/management/commands/init_tipos_proveedor.py
from django.core.management.base import BaseCommand
from compras.models import TipoProveedor

class Command(BaseCommand):
    help = 'Inicializa los tipos de proveedor básicos'

    def handle(self, *args, **kwargs):
        tipos_base = [
            {
                'nombre': 'Proveedor de Frutas',
                'descripcion': 'Proveedores de materia prima (frutas)',
                'es_materia_prima': True
            },
            {
                'nombre': 'Proveedor de Productos Varios',
                'descripcion': 'Proveedores de insumos y otros productos',
                'es_materia_prima': False
            }
        ]

        for tipo in tipos_base:
            tipo_proveedor, created = TipoProveedor.objects.get_or_create(
                nombre=tipo['nombre'],
                defaults={
                    'descripcion': tipo['descripcion'],
                    'es_materia_prima': tipo['es_materia_prima'],
                    'activo': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Creado tipo de proveedor: {tipo["nombre"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'El tipo de proveedor {tipo["nombre"]} ya existe'))