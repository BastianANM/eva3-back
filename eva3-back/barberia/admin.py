from django.contrib import admin

from .models import Barbero, DetalleReserva, Especialidad, Perfil, Servicio, SolicitudReserva


admin.site.site_header = "Navaja Norte - Panel de Control"
admin.site.site_title = "Navaja Norte Admin"
admin.site.index_title = "Gestión Operativa de Recursos y Servicios"


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "especialidad", "precio", "estado", "activo")
    list_filter = ("especialidad", "estado", "activo")
    search_fields = ("codigo", "nombre", "descripcion", "especialidad__nombre")
    list_editable = ("precio", "estado", "activo")
    prepopulated_fields = {"slug": ("nombre",)}
    fieldsets = (
        ("Identificación", {"fields": ("codigo", "nombre", "slug", "especialidad")}),
        ("Detalle y tarifa", {"fields": ("descripcion", "precio", "duracion_minutos", "imagen")}),
        ("Operación", {"fields": ("estado", "activo")}),
    )


@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre", "descripcion")
    prepopulated_fields = {"slug": ("nombre",)}


@admin.register(Barbero)
class BarberoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "telefono", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "presentacion")
    prepopulated_fields = {"slug": ("nombre",)}


class DetalleReservaInline(admin.TabularInline):
    model = DetalleReserva
    extra = 0
    readonly_fields = ("servicio", "barbero", "inicio", "cantidad", "precio_unitario", "duracion_minutos")


@admin.register(SolicitudReserva)
class SolicitudReservaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre_cliente", "email", "estado", "creado")
    list_filter = ("estado", "creado")
    search_fields = ("codigo", "nombre_cliente", "email", "telefono")
    list_editable = ("estado",)
    readonly_fields = ("codigo", "usuario", "nombre_cliente", "email", "telefono", "creado")
    inlines = (DetalleReservaInline,)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rut", "telefono", "rol")
    list_filter = ("rol",)
    search_fields = ("usuario__username", "usuario__email", "rut", "telefono")