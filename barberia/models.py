import uuid
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.utils.text import slugify
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Especialidad(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "especialidad"
        verbose_name_plural = "especialidades"

    def __str__(self):
        return self.nombre


class Barbero(models.Model):
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(max_length=130, unique=True)
    presentacion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    foto = models.ImageField(upload_to="barberos/", blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "barbero"
        verbose_name_plural = "barberos"

    def __str__(self):
        return self.nombre


class Servicio(models.Model):
    class Estado(models.TextChoices):
        DISPONIBLE = "disponible", "Disponible"
        SUSPENDIDO = "suspendido", "Suspendido"

    especialidad = models.ForeignKey(
        Especialidad,
        on_delete=models.PROTECT,
        related_name="servicios"
    )

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    descripcion = models.TextField()

    precio = models.DecimalField(
        max_digits=9,
        decimal_places=0,
        validators=[MinValueValidator(0)]
    )

    duracion_minutos = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )

    estado = models.CharField(
        max_length=12,
        choices=Estado.choices,
        default=Estado.DISPONIBLE
    )

    imagen = models.ImageField(upload_to="servicios/", blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nombre)
            slug = base_slug
            contador = 1

            while Servicio.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{contador}"
                contador += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    class Meta:
        ordering = ["nombre"]
        verbose_name = "servicio"
        verbose_name_plural = "servicios"

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    @property
    def disponible(self):
        return self.activo and self.estado == self.Estado.DISPONIBLE


class Perfil(models.Model):
    class Rol(models.TextChoices):
        CLIENTE = "cliente", "Cliente"
        PERSONAL = "personal", "Personal"

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    rut = models.CharField(max_length=12, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    rol = models.CharField(max_length=12, choices=Rol.choices, default=Rol.CLIENTE)

    def __str__(self):
        return f"Perfil de {self.usuario.get_username()}"


class SolicitudReserva(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente de confirmación"
        CONFIRMADA = "confirmada", "Confirmada"
        ANULADA = "anulada", "Anulada"

    codigo = models.CharField(max_length=12, unique=True, editable=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_cliente = models.CharField(max_length=120)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado"]
        verbose_name = "solicitud de reserva"
        verbose_name_plural = "solicitudes de reserva"

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nombre_cliente}"

    @property
    def subtotal(self):
        return sum((detalle.subtotal for detalle in self.detalles.all()), start=Decimal("0"))

    @property
    def impuesto(self):
        return (self.subtotal * Decimal("0.19")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    @property
    def total(self):
        return self.subtotal + self.impuesto


class DetalleReserva(models.Model):
    solicitud = models.ForeignKey(SolicitudReserva, on_delete=models.CASCADE, related_name="detalles")
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, related_name="reservas")
    barbero = models.ForeignKey(Barbero, on_delete=models.PROTECT, related_name="reservas")
    inicio = models.DateTimeField()
    cantidad = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=9, decimal_places=0, validators=[MinValueValidator(0)])
    duracion_minutos = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ["inicio"]
        verbose_name = "detalle de reserva"
        verbose_name_plural = "detalles de reserva"

    def __str__(self):
        return f"{self.servicio.nombre} - {self.inicio:%d/%m/%Y %H:%M}"

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    @property
    def fin(self):
        return self.inicio + timedelta(minutes=self.duracion_minutos * self.cantidad)