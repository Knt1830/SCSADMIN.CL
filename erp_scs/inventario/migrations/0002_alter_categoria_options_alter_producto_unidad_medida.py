# Generated by Django 5.1.4 on 2024-12-27 06:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='categoria',
            options={'verbose_name': 'Categoría', 'verbose_name_plural': 'Categorías'},
        ),
        migrations.AlterField(
            model_name='producto',
            name='unidad_medida',
            field=models.CharField(choices=[('Kg', 'Kilogramo'), ('Und', 'Unidad'), ('Gamela', 'Gamela')], max_length=10),
        ),
    ]
