
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from functools import wraps
from afacila.models import automatizaciones, plan_suscripcion, suscripciones
from afacila.decoradores import limite_ejecuciones_demo
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

####################################################################################################
#Vista que conecta Django con el webhook de n8n para automatización "Demo campañas de email programadas."
#Los parámetros se envían en un JSON.
from django.http import JsonResponse

@login_requerido
@limite_ejecuciones_demo("Campañas de email programadas")
def demo_campana_envio_email(request):

    #Obtengo la automatización desde la base de datos
    automatizacion = get_object_or_404(automatizaciones, nombre="Campañas de email programadas")
    url = automatizacion.url_demo_webhook

    if request.method == 'POST':
        #Leo el CSV y extraigo emails para enviar al webhook.
        csv_file = request.FILES.get('csv_file')
        emails = []
        mensaje_error = None

        if csv_file:

            #Se comprueba que el fichero sea un CSV válido
            if not csv_file.name.endswith('.csv'):
                return render(request, 'demo_automatizacion_1.html', {
                    'submitted': True,
                    'error': "Formato de archivo no válido. Por favor, sube un archivo CSV. Puedes descargar la plantilla desde esta misma pantalla.",
                    'automatizacion': automatizacion
                })

            try:
                file_data = StringIO(csv_file.read().decode('utf-8-sig'))
                reader = csv.DictReader(file_data)

                for row in reader:
                    email = row.get('email', '')
                    if email:
                        email = email.strip()
                        if email:
                            emails.append(email)
                if not emails:
                    mensaje_error = "El CSV no contiene emails válidos."
                    return render(request, 'demo_automatizacion_1.html', {
                    'submitted': True,
                    'error': mensaje_error,
                    'automatizacion': automatizacion
                    })

            except Exception as e:
                mensaje_error = f"Error al procesar el CSV: {str(e)}"
                context = {
                    'submitted': True,
                    'error': mensaje_error,
                    'automatizacion': automatizacion
                }
                return render(request, 'demo_automatizacion_1.html', context)
        else:
            mensaje_error = "No se ha subido ningún archivo CSV."
            context = {
                'submitted': True,
                'error': mensaje_error,
                'automatizacion': automatizacion
            }
            return render(request, 'demo_automatizacion_1.html', context)
        
        email_origen = request.POST.get('email_origen').strip()
        asunto = request.POST.get('asunto', '').strip()
        mensaje = request.POST.get('mensaje', '').strip()
        intervalo = request.POST.get('intervalo', '').strip()
        fecha_hora_inicio = request.POST.get('fecha_hora_inicio', '').strip()
        fecha_hora_fin = request.POST.get('fecha_hora_fin', '').strip()
    
        # Calcula, en segundos, el intervalo a partir del intervalo_valor y del intervalo_unidad introducidas por el usuario
        try:
            valor = int(request.POST.get("intervalo_valor"))
            unidad = request.POST.get("intervalo_unidad")

            multiplicadores = {
                "minutos": 60,
                "horas": 3600,
                "dias": 86400,
                "semanas": 604800,
            }

            if unidad not in multiplicadores:
                raise ValueError("Unidad inválida")

            if valor < 1:
                raise ValueError("El intervalo debe ser mayor que 0")

            intervalo = valor * multiplicadores[unidad]
            #print("el intervalo es: ", intervalo)

        except Exception as e:
            return render(request, 'demo_automatizacion_1.html', {
                'submitted': True,
                'error': f"Intervalo inválido: {str(e)}",
                'automatizacion': automatizacion
            })


        data = {
            "demo": True,
            "email_origen": email_origen,
            "destinatarios": emails,
            "asunto": asunto,
            "mensaje": mensaje,
            "intervalo": intervalo,
            "fecha_hora_inicio": fecha_hora_inicio,
            "fecha_hora_fin": fecha_hora_fin,
        }

        status = None
        mensaje_error = None

        
        try:
            response = requests.post(url, json=data, timeout=5)
            status = response.status_code
        except Exception as e:
            mensaje_error = str(e)

        context = {
            'submitted': True,
            'status': status,
            'error': mensaje_error,
            'emails_count': len(emails),
            'asunto': asunto,
            'mensaje': mensaje,
            'intervalo': intervalo,
            'fecha_hora_inicio': fecha_hora_inicio,
            'fecha_hora_fin': fecha_hora_fin,
            'automatizacion': automatizacion,
            'email_origen': email_origen,
        }
        return render(request, 'demo_automatizacion_1.html', context)

    # GET y cualquier otro método renderiza el formulario vacío
    return render(request, 'demo_automatizacion_1.html', {'automatizacion': automatizacion})

###############################################################################################

#Vista encargada de simular la venta de la automatización "Campañas de email programadas"   
@login_requerido
def compra_campana_envio_email(request):

    if request.method == 'POST':
        usuario = request.user

        #Obtengo la automatización
        automatizacion = get_object_or_404(automatizaciones, nombre="Campañas de email programadas")

        #Obtengo el tipo de plan seleccionado
        tipo_plan = request.POST.get('plan_suscripcion', 'Mensual')

        #Compruebo que no haya comprado ya la automatización
        existe = suscripciones.objects.filter(usuario=usuario, plan__automatizacion=automatizacion).exists()
        
        if existe:
            messages.error(request, "Ya has comprado esta automatización.")
            return redirect('catalogo')

        #Obtengo el plan de suscripción seleccionado
        plan = get_object_or_404(
            plan_suscripcion, 
            automatizacion=automatizacion, 
            tipo_suscripcion=tipo_plan
        )

        #Calculo la fecha de caducidad según el tipo de plan
        if plan.tipo_suscripcion == 'Mensual':
            fecha_caducidad = date.today() + relativedelta(months=1)
        else:  # Anual
            fecha_caducidad = date.today() + relativedelta(years=1)

        #Creo la suscripción
        try:
            suscripciones.objects.create(
                automatizacion=automatizacion,
                plan=plan,
                usuario=usuario,
                activada=False,
                fecha_caducidad=fecha_caducidad
            )
            messages.success(request, "Automatización comprada correctamente. A partir de este momento podrás gestionarla desde el menú <Mis automatizaciones>, en la pantalla Inicio")
        except Exception as e:
            messages.error(request, f"Error al procesar la compra: {str(e)}")
            return redirect('catalogo')
    
    return redirect('catalogo')

####################################################################################
@login_requerido
def activa_campana_envio_email(request):

    #Obtengo la automatización desde la base de datos
    automatizacion = get_object_or_404(automatizaciones, nombre="Campañas de email programadas")
    url = automatizacion.url_webhook

    if request.method == 'POST':
        #Leo el CSV y extraigo emails para enviar al webhook.
        csv_file = request.FILES.get('csv_file')
        emails = []
        mensaje_error = None

        if csv_file:

            #Se comprueba que el fichero sea un CSV válido
            if not csv_file.name.endswith('.csv'):
                return render(request, 'demo_automatizacion_1.html', {
                    'submitted': True,
                    'error': "Formato de archivo no válido. Por favor, sube un archivo CSV. Puedes descargar la plantilla desde esta misma pantalla.",
                    'automatizacion': automatizacion
                })

            try:
                file_data = StringIO(csv_file.read().decode('utf-8-sig'))
                reader = csv.DictReader(file_data)

                for row in reader:
                    email = row.get('email', '')
                    if email:
                        email = email.strip()
                        if email:
                            emails.append(email)
                if not emails:
                    mensaje_error = "El CSV no contiene emails válidos."
                    return render(request, 'demo_automatizacion_1.html', {
                    'submitted': True,
                    'error': mensaje_error,
                    'automatizacion': automatizacion
                    })

            except Exception as e:
                mensaje_error = "No se ha podido leer el archivo. Asegúrate de que es un CSV válido. Puedes descargar la plantilla desde esta misma pantalla"
                context = {
                    'submitted': True,
                    'error': mensaje_error,
                    'automatizacion': automatizacion
                }
                return render(request, 'demo_automatizacion_1.html', context)
        else:
            mensaje_error = "No se ha subido ningún archivo CSV."
            context = {
                'submitted': True,
                'error': mensaje_error,
                'automatizacion': automatizacion
            }
            return render(request, 'demo_automatizacion_1.html', context)
        
        email_origen = request.POST.get('email_origen').strip()
        asunto = request.POST.get('asunto', '').strip()
        mensaje = request.POST.get('mensaje', '').strip()
        intervalo = request.POST.get('intervalo', '').strip()
        fecha_hora_inicio = request.POST.get('fecha_hora_inicio', '').strip()
        fecha_hora_fin = request.POST.get('fecha_hora_fin', '').strip()
    
        # Calcula, en segundos, el intervalo a partir del intervalo_valor y del intervalo_unidad introducidas por el usuario
        try:
            valor = int(request.POST.get("intervalo_valor"))
            unidad = request.POST.get("intervalo_unidad")

            multiplicadores = {
                "minutos": 60,
                "horas": 3600,
                "dias": 86400,
                "semanas": 604800,
            }

            if unidad not in multiplicadores:
                raise ValueError("Unidad inválida")

            if valor < 1:
                raise ValueError("El intervalo debe ser mayor que 0")

            intervalo = valor * multiplicadores[unidad]
            #print("el intervalo es: ", intervalo)
            
        except Exception as e:
            return render(request, 'demo_automatizacion_1.html', {
                'submitted': True,
                'error': f"Intervalo inválido: {str(e)}",
                'automatizacion': automatizacion
            })


        data = {
            "demo": True,
            "email_origen": email_origen,
            "destinatarios": emails,
            "asunto": asunto,
            "mensaje": mensaje,
            "intervalo": intervalo,
            "fecha_hora_inicio": fecha_hora_inicio,
            "fecha_hora_fin": fecha_hora_fin,
        }

        status = None
        mensaje_error = None

        
        try:
            response = requests.post(url, json=data, timeout=5)
            status = response.status_code
        except Exception as e:
            mensaje_error = str(e)

        context = {
            'submitted': True,
            'status': status,
            'error': mensaje_error,
            'emails_count': len(emails),
            'asunto': asunto,
            'mensaje': mensaje,
            'intervalo': intervalo,
            'fecha_hora_inicio': fecha_hora_inicio,
            'fecha_hora_fin': fecha_hora_fin,
            'automatizacion': automatizacion,
            'email_origen': email_origen,
        }
        return render(request, 'demo_automatizacion_1.html', context)

    # GET y cualquier otro método renderiza el formulario vacío
    return render(request, 'demo_automatizacion_1.html', {'automatizacion': automatizacion})
