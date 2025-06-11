from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Usuario

class RegistroForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['name', 'apellidos', 'telefono', 'email', 'password1', 'password2']
        labels = {
            'name': _('Nombre'),
            'apellidos': _('Apellidos'),
            'telefono': _('Teléfono'),
            'email': _('Correo electrónico'),
            'password1': _('Contraseña'),
            'password2': _('Confirmar contraseña'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs.update({
            'placeholder': 'Escribe tu nombre'
        })
        self.fields['apellidos'].widget.attrs.update({
            'placeholder': 'Escribe tus apellidos'
        })
        self.fields['telefono'].widget.attrs.update({
            'placeholder': 'Número de teléfono'
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Tu correo electrónico'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Crea una contraseña segura'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Repite la contraseña'
        })

        # Traducción de errores comunes de contraseña
        self.fields['password1'].error_messages = {
            'password_too_short': "La contraseña debe tener al menos 8 caracteres.",
            'password_too_common': "La contraseña es demasiado común.",
            'password_entirely_numeric': "La contraseña no puede ser completamente numérica.",
        }

        self.fields['password2'].error_messages = {
            'password_mismatch': "Las contraseñas no coinciden.",
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError("Ya existe una cuenta con este correo electrónico.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Tu correo electrónico'
        })
    )

    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Tu contraseña'
        })
    )


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Introduce tu correo electrónico para recuperar la contraseña",
                            widget=forms.EmailInput(attrs={'placeholder': 'Tu correo electrónico'}))
    

class CambiarPasswordForm(forms.Form):
    label = "Cambiar contraseña"
    password = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Introduce tu nueva contraseña'})
    )
    password2 = forms.CharField(
        label='Repite la nueva contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repite la nueva contraseña'})
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("password2")

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")

        return cleaned_data
