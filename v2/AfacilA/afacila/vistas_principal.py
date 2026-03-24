import http
#from urllib import response
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjYTk1OTU4Mi02NTI0LTQ2YzQtOWE4Yi0yMTUzMTc5NzU5YTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzczNDQyMDUyfQ.4T7RsQsUwvi4LAjC9jnwuxeqPcGRwTKLUSULMp1tLGc"

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from functools import wraps
from afacila.models import automatizaciones, plan_suscripcion, suscripciones, perfil_usuario
import requests
import csv
from io import StringIO
from datetime import date
from dateutil.relativedelta import relativedelta



def login_requerido(view_func):
    #Decorador para controlar que el usuario se haya logueado.
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para acceder a esta página.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def vista_principal_1(request):
    # Renderiza el template principal.html
    return render(request, "principal.html")


def condiciones(request):
    #Vista que muestra las condiciones de uso.
    return render(request, "condiciones.html")


def privacidad(request):
    #Vista que muestra la política de privacidad.
    return render(request, "privacidad.html")


def vista_login(request):
    #Vista de inicio de sesión utilizando un email y una contraseña.
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        try:
            user = User.objects.get(email__iexact=email)
            if user.check_password(password):
                login(request, user)
                return redirect('inicio')
            else:
                error = 'Usuario o contraseña incorrectos.'
        except User.DoesNotExist:
            error = 'Usuario o contraseña incorrectos.'
    return render(request, 'login.html', {'error': error})


def vista_registro(request):
    #Vista que permite registrar un usuario usando el email como nombre de usuario
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not email or not password1:
            error = 'Por favor, cumplimenta todos los campos.'
        elif password1 != password2:
            error = 'Las contraseñas no coinciden.'
        elif User.objects.filter(email__iexact=email).exists():
            error = 'Ya existe en el sistema un usuario con ese correo.'
        else:
            user = User.objects.create_user(username=email, email=email, password=password1)
            perfil_usuario.objects.create(user=user)
            #user.save()
            return redirect('login')

    return render(request, 'registro.html', {'error': error})

def catalogo(request):
    #Vista del catálogo de automatizaciones.
    automatizacion = automatizaciones.objects.filter(nombre="Campañas de email programadas").first()
    planes = plan_suscripcion.objects.filter(automatizacion=automatizacion) if automatizacion else []
    context = {
        'automatizacion': automatizacion,
        'planes': planes
    }
    return render(request, "catalogo.html", context)


#Vista que conecta Django con el webhook de n8n para automatización "Campañas de email programadas."
#Los parámetros se envían en un JSON.
from django.http import JsonResponse

###################################################################################
#Vista que muestra las automatizaciones compradas por el usuario.
@login_requerido
def mis_automatizaciones(request):
    usuario = request.user
    suscripciones_usuario = suscripciones.objects.filter(usuario=usuario)

    if not suscripciones_usuario.exists():
        messages.info(request, "No has comprado ninguna automatización.")
        return redirect('catalogo')
    
    # Preparamos las URLs de configuración para cada suscripción
    for sub in suscripciones_usuario:
        nombre_vista = sub.automatizacion.nombre_vista
        if nombre_vista:
            try:
                sub.config_url = reverse(nombre_vista)
            except Exception as e:
                print(f"Error con reverse({nombre_vista}): {e}")
                sub.config_url = None
        else:
            sub.config_url = None
    
    context = {
        'suscripciones': suscripciones_usuario
    }
    return render(request, 'mis_automatizaciones.html', context)

####################################################################################
#Recupera, desde la base de datos, las suscripciones del usuario dejando el resultado en suscripciones.
#Si no existe ninguna, lanza automáticamente un HTTP 404.
#Si existe, cambia el estado de activada a desactivada o viceversa y guarda el cambio en la base de datos. 
@login_requerido
def activar_desactivar_suscripcion(request, id_suscripcion):

    suscripcion = get_object_or_404(
        suscripciones,
        id=id_suscripcion,
        usuario=request.user
    )

    automatizacion = suscripcion.automatizacion
    #url_desactivacion = automatizacion.url_webhook_parada

    if suscripcion.activada:
        #Reflejo la desactivación en la base de datos. Esto se consultará desde el webhook para saber si seguir ejecutando el bucle o si parar
        suscripcion.activada = False
        suscripcion.save()

        # Desactivo la automatización enviando petición al webhook para detener
        id_ejecucion_n8n = suscripcion.id_ejecucion_n8n

        '''
        #No para en esta automatización por el bucle pero voy a usarlo en las siguientes.
        try:
            urln8n = f"http://localhost:5678/api/v1/executions/{id_ejecucion_n8n}/stop"
            response = requests.delete(
                urln8n,
                headers={
                    "accept": "application/json",
                    "X-N8N-API-KEY": API_KEY
                    }
                )
            if response.status_code == 200:
                print("Automatización detenida exitosamente.")
            else:
                print(f"Error al detener automatización: {response.status_code} - {response.text}")
        except Exception as e:
            print("Error al detener automatización:", e)
        '''
        
        #messages.success(request, "Automatización desactivada.")

        
        
        return redirect('mis_automatizaciones')

    else:
        # Activo la automatización
        suscripcion.activada = True
        suscripcion.save()

        messages.info(request, "Configura la automatización.")

        # redirijo al formulario que recoge los datos
        return redirect(automatizacion.nombre_vista)

###############################################################################
#Vista que devuelve el estado de la suscripción en formato JSON para que el webhook pueda consultarlo en la primera automatización.
#Si la suscripción está activa, el webhook seguirá ejecutándose y si no el webhook parará.
def estado_suscripcion(request, id_suscripcion):
    suscripcion = get_object_or_404(
        suscripciones,
        id=id_suscripcion,
    )
    if suscripcion.activada:
        return JsonResponse({'activada': "activada"}) #Mejor así porque el webhook traduce true a verdadero y genera problemas.
    else:
        return JsonResponse({'activada': "desactivada"})
