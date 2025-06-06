from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Usuario

class RegistroForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['name', 'apellidos', 'telefono', 'email']

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')
