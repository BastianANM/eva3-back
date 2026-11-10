from datetime import datetime, time, timedelta

from django.utils import timezone

from .models import DetalleReserva, SolicitudReserva


HORA_APERTURA = time(9, 0)
HORA_CIERRE = time(20, 0)
SESSION_KEY = "reserva_barberia"


def fecha_hora_local(fecha, hora):
    return timezone.make_aware(datetime.combine(fecha, hora), timezone.get_current_timezone())


def revisar_disponibilidad(barbero, inicio, duracion_minutos, sesion, excluir_clave=None):
    if inicio <= timezone.now():
        return "La hora debe estar en el futuro."
    if inicio.weekday() == 6 or inicio.time() < HORA_APERTURA:
        return "La barbería atiende de lunes a sábado, entre las 09:00 y las 20:00."
    fin = inicio + timedelta(minutes=duracion_minutos)
    cierre = fecha_hora_local(inicio.date(), HORA_CIERRE)
    if fin > cierre or inicio.minute not in (0, 30) or inicio.second or inicio.microsecond:
        return "El horario debe comenzar en punto o a la media hora y terminar antes del cierre."

    reservas = DetalleReserva.objects.select_related("solicitud").filter(
        barbero=barbero,
        inicio__date=inicio.date(),
        solicitud__estado=SolicitudReserva.Estado.CONFIRMADA,
    )
    for reserva in reservas:
        reserva_fin = reserva.inicio + timedelta(minutes=reserva.duracion_minutos * reserva.cantidad)
        if inicio < reserva_fin and fin > reserva.inicio:
            return "Ese barbero ya tiene una reserva en ese bloque horario."

    for clave, item in sesion.items():
        if clave == excluir_clave or str(item["barbero_id"]) != str(barbero.pk):
            continue
        item_inicio = fecha_hora_local(
            datetime.strptime(item["fecha"], "%Y-%m-%d").date(),
            datetime.strptime(item["hora"], "%H:%M").time(),
        )
        item_fin = item_inicio + timedelta(minutes=int(item["duracion"]) * int(item["cantidad"]))
        if inicio < item_fin and fin > item_inicio:
            return "Tu planificación ya contiene una atención de ese barbero en ese bloque."
    return ""