from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("", views.catalogo, name="catalogo"),
    path("servicio/<slug:slug>/", views.detalle_servicio, name="detalle_servicio"),
    path("reserva/", views.reserva, name="reserva"),
    path("reserva/agregar/", views.agregar_reserva, name="agregar_reserva"),
    path("reserva/actualizar/", views.actualizar_reserva, name="actualizar_reserva"),
    path("reserva/quitar/<path:clave>/", views.quitar_reserva, name="quitar_reserva"),
    path("reserva/vaciar/", views.vaciar_reserva, name="vaciar_reserva"),
    path("reserva/enviar/", views.enviar_solicitud, name="enviar_solicitud"),
    path("comprobante/<str:codigo>/", views.comprobante, name="comprobante"),
    path("cuenta/registro/", views.registro, name="registro"),
    path("cuenta/ingresar/", auth_views.LoginView.as_view(template_name="barberia/login.html"), name="login"),
    path("cuenta/salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("cuenta/perfil/", views.perfil, name="perfil"),
    path("gestion/servicios/", views.gestion_servicios, name="gestion_servicios"),
    path("gestion/servicios/nuevo/", views.crear_servicio, name="crear_servicio"),
    path("gestion/servicios/<int:pk>/editar/", views.editar_servicio, name="editar_servicio"),
    path("gestion/servicios/<int:pk>/baja/", views.eliminar_servicio, name="eliminar_servicio"),
]