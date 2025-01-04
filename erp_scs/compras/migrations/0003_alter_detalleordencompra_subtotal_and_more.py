# Generated by Django 5.1.4 on 2024-12-29 04:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0002_producto_productoproveedor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='detalleordencompra',
            name='subtotal',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='ordencompra',
            name='impuestos',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='ordencompra',
            name='numero_orden',
            field=models.CharField(help_text='Formato: OC-YYYY-NNNN', max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name='ordencompra',
            name='subtotal',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='ordencompra',
            name='total',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
