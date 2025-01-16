# inventario/management/commands/init_categorias.py
from django.core.management.base import BaseCommand
from inventario.models import Categoria

class Command(BaseCommand):
    help = 'Inicializa las categorías base del sistema'

    def handle(self, *args, **kwargs):
        # Solo las categorías principales
        categorias = [
            ('FRU', 'Frutas'),
            ('ENV', 'Envases'),
            ('MIS', 'Misceláneos')
        ]
        
        for tipo, nombre in categorias:
            categoria, created = Categoria.objects.get_or_create(
                tipo=tipo,
                nombre=nombre
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Creada categoría: {nombre}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'La categoría {nombre} ya existe')
                )