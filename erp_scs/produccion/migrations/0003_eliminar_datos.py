from django.db import migrations

def eliminar_todo_contenido(apps, schema_editor):
    # Eliminamos ProduccionDiaria primero ya que depende de los otros modelos
    ProduccionDiaria = apps.get_model('produccion', 'ProduccionDiaria')
    ProduccionDiaria.objects.all().delete()

    # Eliminamos ProcesoProduccion 
    ProcesoProduccion = apps.get_model('produccion', 'ProcesoProduccion')
    ProcesoProduccion.objects.all().delete()

    # Eliminamos TrabajadorProduccion
    TrabajadorProduccion = apps.get_model('produccion', 'TrabajadorProduccion')
    TrabajadorProduccion.objects.all().delete()

def revertir_eliminacion(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('produccion', '0002_remove_procesoproduccion_merma_and_more'),  # Asegúrate de poner aquí tu última migración
    ]

    operations = [
        migrations.RunPython(
            eliminar_todo_contenido,
            revertir_eliminacion
        ),
    ]