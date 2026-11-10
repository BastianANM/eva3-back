from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import RegistroForm, ServicioForm, SolicitudForm
from .models import Barbero, DetalleReserva, Especialidad, Perfil, Servicio, SolicitudReserva
from .services import SESSION_KEY, fecha_hora_local, revisar_disponibilidad


def catalogo(request):
    servicios = Servicio.objects.filter(
        activo=True,
        estado=Servicio.Estado.DISPONIBLE,
        especialidad__activa=True,
    ).select_related("especialidad")
    consulta = request.GET.get("q", "").strip()
    especialidad_id = request.GET.get("especialidad", "")
    orden = request.GET.get("orden", "nombre")
    if consulta:
        servicios = servicios.filter(
            Q(nombre__icontains=consulta)
            | Q(codigo__icontains=consulta)
            | Q(descripcion__icontains=consulta)
        )
    if especialidad_id.isdigit():
        servicios = servicios.filter(especialidad_id=especialidad_id)
    if orden not in {"nombre", "precio", "-precio", "duracion_minutos"}:
        orden = "nombre"
    pagina = Paginator(servicios.order_by(orden, "nombre"), 6).get_page(request.GET.get("page"))
    return render(request, "barberia/catalogo.html", {
        "pagina": pagina,
        "consulta": consulta,
        "especialidad_seleccionada": especialidad_id,
        "especialidades": Especialidad.objects.filter(activa=True),
        "orden": orden,
    })


def detalle_servicio(request, slug):
    servicio = get_object_or_404(
        Servicio.objects.select_related("especialidad"),
        slug=slug,
        activo=True,
        estado=Servicio.Estado.DISPONIBLE,
    )
    return render(request, "barberia/detalle.html", {"servicio": servicio, "barberos": Barbero.objects.filter(activo=True)})


def agregar_reserva(request):
    if request.method != "POST":
        return redirect("catalogo")
    servicio = get_object_or_404(Servicio, pk=request.POST.get("servicio_id"), activo=True, estado=Servicio.Estado.DISPONIBLE)
    barbero = get_object_or_404(Barbero, pk=request.POST.get("barbero_id"), activo=True)
    try:
        fecha = datetime.strptime(request.POST.get("fecha", ""), "%Y-%m-%d").date()
        hora = datetime.strptime(request.POST.get("hora", ""), "%H:%M").time()
        cantidad = int(request.POST.get("cantidad", "1"))
        if not 1 <= cantidad <= 4:
            raise ValueError
    except (TypeError, ValueError):
        messages.error(request, "Revisa la fecha, la hora y la cantidad solicitada.")
        return redirect("detalle_servicio", slug=servicio.slug)

    items = request.session.get(SESSION_KEY, {})
    clave = f"{servicio.pk}:{barbero.pk}:{fecha.isoformat()}:{hora.strftime('%H:%M')}"
    cantidad_total = cantidad + int(items.get(clave, {}).get("cantidad", 0))
    if cantidad_total > 4:
        messages.error(request, "Puedes planificar hasta 4 unidades por servicio y horario.")
        return redirect("detalle_servicio", slug=servicio.slug)
    inicio = fecha_hora_local(fecha, hora)
    error = revisar_disponibilidad(barbero, inicio, servicio.duracion_minutos * cantidad_total, items, excluir_clave=clave)
    if error:
        messages.error(request, error)
        return redirect("detalle_servicio", slug=servicio.slug)

    items[clave] = {
        "servicio_id": servicio.pk,
        "barbero_id": barbero.pk,
        "fecha": fecha.isoformat(),
        "hora": hora.strftime("%H:%M"),
        "cantidad": cantidad_total,
        "duracion": servicio.duracion_minutos,
    }
    request.session[SESSION_KEY] = items
    request.session.modified = True
    messages.success(request, "Servicio agregado a tu solicitud temporal.")
    return redirect("reserva")


def _resumen_items(request):
    items = request.session.get(SESSION_KEY, {})
    resumen = []
    subtotal = Decimal("0")
    for clave, item in items.items():
        servicio = Servicio.objects.filter(pk=item["servicio_id"], activo=True).first()
        barbero = Barbero.objects.filter(pk=item["barbero_id"], activo=True).first()
        if not servicio or not barbero:
            continue
        cantidad = int(item["cantidad"])
        importe = servicio.precio * cantidad
        subtotal += importe
        resumen.append({
            "clave": clave,
            "servicio": servicio,
            "barbero": barbero,
            "fecha": datetime.strptime(item["fecha"], "%Y-%m-%d").date(),
            "hora": item["hora"],
            "cantidad": cantidad,
            "duracion_total": servicio.duracion_minutos * cantidad,
            "importe": importe,
        })
    impuesto = (subtotal * Decimal("0.19")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return resumen, subtotal, impuesto, subtotal + impuesto


def reserva(request):
    lineas, subtotal, impuesto, total = _resumen_items(request)
    return render(request, "barberia/reserva.html", {
        "lineas": lineas,
        "subtotal": subtotal,
        "impuesto": impuesto,
        "total": total,
    })


def actualizar_reserva(request):
    if request.method != "POST":
        return redirect("reserva")
    clave = request.POST.get("clave", "")
    items = request.session.get(SESSION_KEY, {})
    item = items.get(clave)
    if not item:
        messages.error(request, "No encontramos ese servicio en la solicitud.")
        return redirect("reserva")
    try:
        cantidad = int(request.POST.get("cantidad", "1"))
        if not 1 <= cantidad <= 4:
            raise ValueError
        servicio = get_object_or_404(Servicio, pk=item["servicio_id"], activo=True, estado=Servicio.Estado.DISPONIBLE)
        barbero = get_object_or_404(Barbero, pk=item["barbero_id"], activo=True)
        inicio = fecha_hora_local(
            datetime.strptime(item["fecha"], "%Y-%m-%d").date(),
            datetime.strptime(item["hora"], "%H:%M").time(),
        )
    except (TypeError, ValueError):
        messages.error(request, "La cantidad debe estar entre 1 y 4.")
        return redirect("reserva")
    error = revisar_disponibilidad(barbero, inicio, servicio.duracion_minutos * cantidad, items, excluir_clave=clave)
    if error:
        messages.error(request, error)
    else:
        item["cantidad"] = cantidad
        items[clave] = item
        request.session[SESSION_KEY] = items
        request.session.modified = True
        messages.success(request, "Solicitud actualizada.")
    return redirect("reserva")


def quitar_reserva(request, clave):
    if request.method == "POST":
        items = request.session.get(SESSION_KEY, {})
        items.pop(clave, None)
        request.session[SESSION_KEY] = items
        request.session.modified = True
        messages.info(request, "Servicio quitado de tu solicitud.")
    return redirect("reserva")


def vaciar_reserva(request):
    if request.method == "POST":
        request.session.pop(SESSION_KEY, None)
        messages.info(request, "La solicitud temporal quedó vacía.")
    return redirect("reserva")


def enviar_solicitud(request):
    lineas, subtotal, impuesto, total = _resumen_items(request)
    if not lineas:
        messages.error(request, "Agrega al menos un servicio antes de enviar la solicitud.")
        return redirect("catalogo")
    initial = {}
    if request.user.is_authenticated:
        initial = {
            "nombre_cliente": request.user.get_full_name() or request.user.username,
            "email": request.user.email,
        }
        perfil = Perfil.objects.filter(usuario=request.user).first()
        if perfil:
            initial["telefono"] = perfil.telefono
    form = SolicitudForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        items = request.session.get(SESSION_KEY, {})
        with transaction.atomic():
            solicitud = SolicitudReserva.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                nombre_cliente=form.cleaned_data["nombre_cliente"],
                email=form.cleaned_data["email"],
                telefono=form.cleaned_data["telefono"],
            )
            for linea in lineas:
                item = items.get(linea["clave"])
                if not item:
                    continue
                servicio = linea["servicio"]
                barbero = linea["barbero"]
                inicio = fecha_hora_local(linea["fecha"], datetime.strptime(linea["hora"], "%H:%M").time())
                error = revisar_disponibilidad(
                    barbero,
                    inicio,
                    servicio.duracion_minutos * linea["cantidad"],
                    items,
                    excluir_clave=linea["clave"],
                )
                if error:
                    transaction.set_rollback(True)
                    messages.error(request, error)
                    return redirect("reserva")
                DetalleReserva.objects.create(
                    solicitud=solicitud,
                    servicio=servicio,
                    barbero=barbero,
                    inicio=inicio,
                    cantidad=linea["cantidad"],
                    precio_unitario=servicio.precio,
                    duracion_minutos=servicio.duracion_minutos,
                )
        request.session.pop(SESSION_KEY, None)
        request.session["ultimo_comprobante"] = solicitud.codigo
        messages.success(request, "Solicitud recibida. El equipo confirmará la hora por contacto directo.")
        return redirect("comprobante", codigo=solicitud.codigo)
    return render(request, "barberia/checkout.html", {
        "form": form,
        "lineas": lineas,
        "subtotal": subtotal,
        "impuesto": impuesto,
        "total": total,
    })


def comprobante(request, codigo):
    solicitud = get_object_or_404(
        SolicitudReserva.objects.prefetch_related("detalles__servicio", "detalles__barbero"),
        codigo=codigo,
    )
    if request.session.get("ultimo_comprobante") != solicitud.codigo and (
        not request.user.is_authenticated or solicitud.usuario_id != request.user.pk
    ):
        messages.error(request, "No tienes acceso a este comprobante.")
        return redirect("catalogo")
    return render(request, "barberia/comprobante.html", {"solicitud": solicitud})


def registro(request):
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, "Tu cuenta está lista.")
        return redirect("catalogo")
    return render(request, "barberia/registro.html", {"form": form})


@login_required
def perfil(request):
    perfil_usuario, _ = Perfil.objects.get_or_create(usuario=request.user)
    return render(request, "barberia/perfil.html", {"perfil": perfil_usuario})


def es_personal(usuario):
    return usuario.is_staff


@login_required
@user_passes_test(es_personal)
def gestion_servicios(request):
    servicios = Servicio.objects.select_related("especialidad").order_by("nombre")
    return render(request, "barberia/gestion.html", {"servicios": servicios})


@login_required
@user_passes_test(es_personal)
def crear_servicio(request):
    form = ServicioForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        servicio = form.save()
        messages.success(request, "Servicio creado correctamente.")
        return redirect("gestion_servicios")
    return render(request, "barberia/form_servicio.html", {"form": form, "titulo": "Nuevo servicio"})


@login_required
@user_passes_test(es_personal)
def editar_servicio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    form = ServicioForm(request.POST or None, request.FILES or None, instance=servicio)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Servicio actualizado correctamente.")
        return redirect("gestion_servicios")
    return render(request, "barberia/form_servicio.html", {"form": form, "titulo": "Editar servicio", "servicio": servicio})


@login_required
@user_passes_test(es_personal)
def eliminar_servicio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == "POST":
        servicio.activo = False
        servicio.save(update_fields=["activo"])
        messages.success(request, "Servicio desactivado; sus datos históricos se conservaron.")
        return redirect("gestion_servicios")
    return render(request, "barberia/confirmar_baja.html", {"servicio": servicio})