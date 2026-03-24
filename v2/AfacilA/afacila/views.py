from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages

# Create your views here.

def vista_principal_1(request):
    # Renderiza el template base.html
    return render(request, "vista_principal.html")


def condiciones(request):
    """Vista que muestra las condiciones de uso."""
    return render(request, "condiciones.html")


def privacidad(request):
    """Vista que muestra la política de privacidad."""
    return render(request, "privacidad.html")


def vista_login(request):
    """Vista de inicio de sesión por email y contraseña."""
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        try:
            user = User.objects.get(email__iexact=email)
            if user.check_password(password):
                login(request, user)
                return redirect('vista_principal_1')
            else:
                error = 'Usuario o contraseña incorrectos.'
        except User.DoesNotExist:
            error = 'Usuario o contraseña incorrectos.'
    return render(request, 'login.html', {'error': error})


def registro_view(request):
    """Vista de registro: crea un usuario usando email como username."""
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not email or not password1:
            error = 'Rellena todos los campos.'
        elif password1 != password2:
            error = 'Las contraseñas no coinciden.'
        elif User.objects.filter(email__iexact=email).exists():
            error = 'Ya existe un usuario con ese correo.'
        else:
            # usar email como username
            user = User.objects.create_user(username=email, email=email, password=password1)
            user.save()
            return redirect('login')

    return render(request, 'registro.html', {'error': error})

