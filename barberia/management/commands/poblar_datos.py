from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from barberia.models import Barbero, Especialidad, Perfil, Servicio


class Command(BaseCommand):
    help = "Carga especialidades, servicios, barberos y cuentas de demostración."

    def handle(self, *args, **options):
        especialidades = [
            ("Corte", "Cortes clásicos y contemporáneos."),
            ("Barba", "Perfilado, afeitado y cuidado de barba."),
            ("Tratamientos", "Rituales de cuidado y bienestar capilar."),
            ("Experiencias", "Combinaciones y servicios especiales."),
        ]
        categorias = {}
        for nombre, descripcion in especialidades:
            categoria, _ = Especialidad.objects.update_or_create(
                slug=slugify(nombre),
                defaults={"nombre": nombre, "descripcion": descripcion, "activa": True},
            )
            categorias[nombre] = categoria

        barberos = [
            ("Matías Rojas", "matias-rojas", "Especialista en tijera y degradados."),
            ("Antonia Fuentes", "antonia-fuentes", "Cortes de precisión y diseño."),
            ("Diego Salas", "diego-salas", "Afeitado clásico y cuidado de barba."),
        ]
        for nombre, slug, presentacion in barberos:
            Barbero.objects.update_or_create(slug=slug, defaults={"nombre": nombre, "presentacion": presentacion, "activo": True})

        servicios = [
            ("NN-C01", "Corte clásico", "corte-clasico", "Corte a tijera o máquina, terminado con styling.", "Corte", 12000, 40),
            ("NN-C02", "Degradado", "degradado", "Degradado personalizado con contornos definidos.", "Corte", 15000, 45),
            ("NN-C03", "Corte y lavado", "corte-y-lavado", "Corte completo con lavado y acabado.", "Corte", 16000, 55),
            ("NN-B01", "Perfilado de barba", "perfilado-de-barba", "Diseño de líneas, simetría y aplicación de bálsamo.", "Barba", 9000, 30),
            ("NN-B02", "Afeitado clásico", "afeitado-clasico", "Toalla caliente y afeitado tradicional con navaja.", "Barba", 13000, 40),
            ("NN-T01", "Ritual facial", "ritual-facial", "Limpieza express e hidratación para cerrar la visita.", "Tratamientos", 11000, 30),
            ("NN-T02", "Tratamiento capilar", "tratamiento-capilar", "Masaje y tratamiento nutritivo según tu tipo de cabello.", "Tratamientos", 14000, 35),
            ("NN-E01", "Corte + barba", "corte-mas-barba", "Corte a elección más perfilado de barba.", "Experiencias", 19500, 65),
        ]
        for codigo, nombre, slug, descripcion, categoria, precio, duracion in servicios:
            Servicio.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "especialidad": categorias[categoria],
                    "nombre": nombre,
                    "slug": slug,
                    "descripcion": descripcion,
                    "precio": precio,
                    "duracion_minutos": duracion,
                    "estado": Servicio.Estado.DISPONIBLE,
                    "activo": True,
                },
            )

        admin, admin_creado = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@navajanorte.local", "is_staff": True, "is_superuser": True},
        )
        cliente, cliente_creado = User.objects.get_or_create(
            username="cliente_demo",
            defaults={"email": "cliente@navajanorte.local", "first_name": "Cliente", "last_name": "Demo"},
        )
        if admin_creado:
            admin.set_password("NavajaDemo2026!")
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        if cliente_creado:
            cliente.set_password("ClienteDemo2026!")
            cliente.save()
        Perfil.objects.update_or_create(usuario=admin, defaults={"rol": Perfil.Rol.PERSONAL})
        Perfil.objects.get_or_create(usuario=cliente, defaults={"telefono": "+56911112222"})

        self.stdout.write(self.style.SUCCESS("Datos de demostración cargados: 4 especialidades, 8 servicios, 3 barberos y 2 usuarios."))