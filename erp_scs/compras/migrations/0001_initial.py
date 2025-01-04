# Generated by Django 5.1.4 on 2024-12-30 23:33

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DetalleOrdenCompra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.DecimalField(decimal_places=2, max_digits=10)),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('notas', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Detalle de Orden de Compra',
                'verbose_name_plural': 'Detalles de Orden de Compra',
            },
        ),
        migrations.CreateModel(
            name='HistorialCalibre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_entrega', models.DateField()),
                ('calibre', models.CharField(max_length=50)),
                ('cantidad', models.DecimalField(decimal_places=2, max_digits=10)),
                ('calidad', models.CharField(choices=[('EXCELENTE', 'Excelente'), ('BUENA', 'Buena'), ('REGULAR', 'Regular'), ('DEFICIENTE', 'Deficiente')], max_length=20)),
                ('observaciones', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Historial de Calibre',
                'verbose_name_plural': 'Historial de Calibres',
                'ordering': ['-fecha_entrega'],
            },
        ),
        migrations.CreateModel(
            name='OrdenCompra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_orden', models.CharField(help_text='Formato: OC-YYYY-NNNN', max_length=20, unique=True)),
                ('fecha_emision', models.DateField()),
                ('fecha_entrega_esperada', models.DateField()),
                ('estado', models.CharField(choices=[('BORRADOR', 'Borrador'), ('ENVIADA', 'Enviada'), ('CONFIRMADA', 'Confirmada'), ('RECIBIDA', 'Recibida'), ('CANCELADA', 'Cancelada')], default='BORRADOR', max_length=20)),
                ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('impuestos', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('notas', models.TextField(blank=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('ultima_modificacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Orden de Compra',
                'verbose_name_plural': 'Órdenes de Compra',
                'ordering': ['-fecha_emision'],
            },
        ),
        migrations.CreateModel(
            name='Proveedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('rut', models.CharField(max_length=12, unique=True, validators=[django.core.validators.RegexValidator(message='RUT debe tener formato XX.XXX.XXX-X', regex='^\\d{1,2}\\.\\d{3}\\.\\d{3}-[\\dkK]$')], verbose_name='RUT')),
                ('direccion', models.CharField(max_length=255)),
                ('telefono', models.CharField(max_length=20)),
                ('activo', models.BooleanField(default=True)),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('ultima_modificacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Proveedor',
                'verbose_name_plural': 'Proveedores',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='ProveedorProducto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('precio_referencia', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('es_proveedor_principal', models.BooleanField(default=False)),
                ('notas', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Producto de Proveedor',
                'verbose_name_plural': 'Productos de Proveedores',
            },
        ),
        migrations.CreateModel(
            name='TipoProveedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('descripcion', models.TextField(blank=True)),
                ('es_materia_prima', models.BooleanField(default=False, help_text='Indica si este tipo de proveedor suministra materia prima')),
                ('activo', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Tipo de Proveedor',
                'verbose_name_plural': 'Tipos de Proveedores',
            },
        ),
    ]
