# Generated by Django 5.1.4 on 2024-12-30 23:33

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventario', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre Completo')),
                ('rut', models.CharField(max_length=20, unique=True, verbose_name='RUT')),
                ('telefono', models.CharField(max_length=20, verbose_name='Teléfono')),
                ('direccion', models.TextField(blank=True, null=True, verbose_name='Dirección')),
                ('email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Correo Electrónico')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True)),
                ('usuario_registro', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clientes_registrados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='CreditoCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('monto_total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('monto_pagado', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('fecha_credito', models.DateTimeField(default=django.utils.timezone.now)),
                ('fecha_vencimiento', models.DateField()),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('PARCIAL', 'Pago Parcial'), ('PAGADO', 'Pagado')], default='PENDIENTE', max_length=20)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='creditos', to='ventas.cliente')),
            ],
            options={
                'verbose_name': 'Crédito de Cliente',
                'verbose_name_plural': 'Créditos de Clientes',
                'ordering': ['-fecha_credito'],
            },
        ),
        migrations.CreateModel(
            name='PagoCredito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10)),
                ('fecha_pago', models.DateTimeField(auto_now_add=True)),
                ('observaciones', models.TextField(blank=True)),
                ('credito', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pagos', to='ventas.creditocliente')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Pago de Crédito',
                'verbose_name_plural': 'Pagos de Créditos',
                'ordering': ['-fecha_pago'],
            },
        ),
        migrations.CreateModel(
            name='Venta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_venta', models.DateTimeField(default=django.utils.timezone.now)),
                ('es_credito', models.BooleanField(default=False, verbose_name='Venta a Crédito')),
                ('dias_credito', models.IntegerField(blank=True, null=True, verbose_name='Días de Crédito')),
                ('fecha_vencimiento_credito', models.DateField(blank=True, null=True)),
                ('estado', models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('PAGADA', 'Pagada'), ('ANULADA', 'Anulada')], default='PENDIENTE', max_length=20)),
                ('total_venta', models.DecimalField(decimal_places=2, max_digits=10)),
                ('observaciones', models.TextField(blank=True, null=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ventas', to='ventas.cliente')),
                ('usuario_venta', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ventas_realizadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Venta',
                'verbose_name_plural': 'Ventas',
                'ordering': ['-fecha_venta'],
            },
        ),
        migrations.CreateModel(
            name='DetalleVenta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_producto', models.CharField(max_length=200)),
                ('cantidad', models.DecimalField(decimal_places=2, max_digits=10)),
                ('precio_unitario', models.DecimalField(decimal_places=2, max_digits=10)),
                ('subtotal', models.DecimalField(decimal_places=2, max_digits=10)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='inventario.producto')),
                ('venta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detalles', to='ventas.venta')),
            ],
        ),
        migrations.AddField(
            model_name='creditocliente',
            name='venta',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='ventas.venta'),
        ),
    ]
