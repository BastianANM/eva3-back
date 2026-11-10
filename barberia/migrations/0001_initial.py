import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Barbero",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=130, unique=True)),
                ("presentacion", models.TextField(blank=True)),
                ("telefono", models.CharField(blank=True, max_length=20)),
                ("foto", models.ImageField(blank=True, upload_to="barberos/")),
                ("activo", models.BooleanField(default=True)),
            ],
            options={"verbose_name": "barbero", "verbose_name_plural": "barberos", "ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="Especialidad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(max_length=90, unique=True)),
                ("descripcion", models.TextField(blank=True)),
                ("activa", models.BooleanField(default=True)),
            ],
            options={"verbose_name": "especialidad", "verbose_name_plural": "especialidades", "ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="Perfil",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rut", models.CharField(blank=True, max_length=12)),
                ("telefono", models.CharField(blank=True, max_length=20)),
                ("rol", models.CharField(choices=[("cliente", "Cliente"), ("personal", "Personal")], default="cliente", max_length=12)),
                ("usuario", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="perfil", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Servicio",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(max_length=20, unique=True)),
                ("nombre", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=140, unique=True)),
                ("descripcion", models.TextField()),
                ("precio", models.DecimalField(decimal_places=0, max_digits=9, validators=[django.core.validators.MinValueValidator(0)])),
                ("duracion_minutos", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("estado", models.CharField(choices=[("disponible", "Disponible"), ("suspendido", "Suspendido")], default="disponible", max_length=12)),
                ("imagen", models.ImageField(blank=True, upload_to="servicios/")),
                ("activo", models.BooleanField(default=True)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("especialidad", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="servicios", to="barberia.especialidad")),
            ],
            options={"verbose_name": "servicio", "verbose_name_plural": "servicios", "ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="SolicitudReserva",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("codigo", models.CharField(editable=False, max_length=12, unique=True)),
                ("nombre_cliente", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254)),
                ("telefono", models.CharField(max_length=20)),
                ("estado", models.CharField(choices=[("pendiente", "Pendiente de confirmación"), ("confirmada", "Confirmada"), ("anulada", "Anulada")], default="pendiente", max_length=12)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("usuario", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "solicitud de reserva", "verbose_name_plural": "solicitudes de reserva", "ordering": ["-creado"]},
        ),
        migrations.CreateModel(
            name="DetalleReserva",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("inicio", models.DateTimeField()),
                ("cantidad", models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ("precio_unitario", models.DecimalField(decimal_places=0, max_digits=9, validators=[django.core.validators.MinValueValidator(0)])),
                ("duracion_minutos", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("barbero", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reservas", to="barberia.barbero")),
                ("servicio", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reservas", to="barberia.servicio")),
                ("solicitud", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="detalles", to="barberia.solicitudreserva")),
            ],
            options={"verbose_name": "detalle de reserva", "verbose_name_plural": "detalles de reserva", "ordering": ["inicio"]},
        ),
    ]