from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Perfil, Servicio


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = (
            "especialidad",
            "codigo",
            "nombre",
            "slug",
            "descripcion",
            "precio",
            "duracion_minutos",
            "estado",
            "imagen",
            "activo",
        )
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "imagen": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def clean_codigo(self):
        codigo = self.cleaned_data["codigo"].strip().upper()
        queryset = Servicio.objects.filter(codigo__iexact=codigo)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("Ya existe un servicio con este código.")
        return codigo

    def clean_precio(self):
        precio = self.cleaned_data["precio"]
        if precio < 0:
            raise forms.ValidationError("El precio no puede ser negativo.")
        return precio


class RegistroForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, label="Nombre")
    last_name = forms.CharField(max_length=150, label="Apellido")
    rut = forms.CharField(max_length=12, label="RUT", required=False)
    telefono = forms.CharField(max_length=20, label="Teléfono", required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "rut", "telefono")

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data["email"]
        usuario.first_name = self.cleaned_data["first_name"]
        usuario.last_name = self.cleaned_data["last_name"]
        if commit:
            usuario.save()
            Perfil.objects.create(
                usuario=usuario,
                rut=self.cleaned_data["rut"],
                telefono=self.cleaned_data["telefono"],
            )
        return usuario


class SolicitudForm(forms.Form):
    nombre_cliente = forms.CharField(max_length=120, label="Nombre completo")
    email = forms.EmailField(label="Correo electrónico")
    telefono = forms.CharField(max_length=20, label="Teléfono")