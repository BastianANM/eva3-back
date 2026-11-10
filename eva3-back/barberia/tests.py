from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Barbero, Especialidad, Servicio, SolicitudReserva
from .services import SESSION_KEY


class BarberiaFlowTests(TestCase):
    def setUp(self):
        self.especialidad = Especialidad.objects.create(nombre="Corte", slug="corte")
        self.servicio = Servicio.objects.create(
            especialidad=self.especialidad,
            codigo="TEST-01",
            nombre="Corte de prueba",
            slug="corte-prueba",
            descripcion="Servicio de prueba para el catálogo.",
            precio=12000,
            duracion_minutos=40,
        )
        self.barbero = Barbero.objects.create(nombre="Barbero Demo", slug="barbero-demo")

    def fecha_futura(self):
        fecha = timezone.localdate() + timedelta(days=1)
        while fecha.weekday() == 6:
            fecha += timedelta(days=1)
        return fecha

    def test_precio_negativo_es_invalido(self):
        self.servicio.precio = -1
        with self.assertRaises(ValidationError):
            self.servicio.full_clean()

    def test_catalogo_filtra_por_nombre_codigo_y_descripcion(self):
        response = self.client.get(reverse("catalogo"), {"q": "TEST-01"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Corte de prueba")
        self.assertEqual(len(response.context["pagina"].object_list), 1)

    def test_solicitud_se_guarda_al_enviar_y_vacia_el_carro_temporal(self):
        response = self.client.post(reverse("agregar_reserva"), {
            "servicio_id": self.servicio.pk,
            "barbero_id": self.barbero.pk,
            "fecha": self.fecha_futura().isoformat(),
            "hora": "11:00",
            "cantidad": "1",
        })
        self.assertRedirects(response, reverse("reserva"))
        self.assertEqual(sum(self.client.session[SESSION_KEY][key]["cantidad"] for key in self.client.session[SESSION_KEY]), 1)

        response = self.client.post(reverse("enviar_solicitud"), {
            "nombre_cliente": "Cliente de Prueba",
            "email": "cliente@example.test",
            "telefono": "+56912345678",
        })
        self.assertEqual(response.status_code, 302)
        solicitud = SolicitudReserva.objects.get()
        self.assertEqual(solicitud.estado, SolicitudReserva.Estado.PENDIENTE)
        self.assertEqual(solicitud.detalles.count(), 1)
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertEqual(self.client.session["ultimo_comprobante"], solicitud.codigo)

    def test_sesion_rechaza_horarios_que_se_solapan(self):
        otro_servicio = Servicio.objects.create(
            especialidad=self.especialidad,
            codigo="TEST-02",
            nombre="Barba de prueba",
            slug="barba-prueba",
            descripcion="Segundo servicio para probar disponibilidad.",
            precio=8000,
            duracion_minutos=30,
        )
        fecha = self.fecha_futura().isoformat()
        self.client.post(reverse("agregar_reserva"), {
            "servicio_id": self.servicio.pk,
            "barbero_id": self.barbero.pk,
            "fecha": fecha,
            "hora": "11:00",
            "cantidad": "1",
        })
        response = self.client.post(reverse("agregar_reserva"), {
            "servicio_id": otro_servicio.pk,
            "barbero_id": self.barbero.pk,
            "fecha": fecha,
            "hora": "11:30",
            "cantidad": "1",
        })
        self.assertRedirects(response, reverse("detalle_servicio", args=[otro_servicio.slug]))
        self.assertEqual(len(self.client.session[SESSION_KEY]), 1)

    def test_gestion_requiere_personal_autenticado(self):
        response = self.client.get(reverse("gestion_servicios"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
