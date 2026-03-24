from multiprocessing import context

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from functools import wraps
from afacila.models import automatizaciones, plan_suscripcion, suscripciones, vistaprevia_post
import requests
#import csv
from afacila.decoradores import limite_ejecuciones_demo
from io import StringIO
from datetime import date
from dateutil.relativedelta import relativedelta
from django.http import JsonResponse
from django.contrib import messages


def login_requerido(view_func):
    #Decorador para controlar que el usuario se haya logueado.
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para acceder a esta página.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

#Vista que conecta Django con el webhook de n8n para automatización "Generación automática de post para redes sociales"
#Los parámetros se envían en un JSON.
from django.http import JsonResponse

######################################################################################
@login_requerido
@limite_ejecuciones_demo("Generación automática de post para redes sociales - Telegram")
def demo_generacion_post_redes_sociales(request):
    mensaje_error = None

    #Obtengo la automatización desde la base de datos
    automatizacion = get_object_or_404(automatizaciones, nombre="Generación automática de post para redes sociales - Telegram")
    url = automatizacion.url_webhook

    #Muestra formulario limpio al cargar la página por primera vez o al hacer refresh.
    if request.method == 'GET':
        vistaprevia_post.objects.all().delete()
        return render(request, 'demo_automatizacion_2.html', {'automatizacion': automatizacion, 'webhook_url': url})
   
    #Envía a n8n la descripción y la imagen (si el usuario ha subido alguna) para que n8n la procese y genere el post
    if request.method == 'POST':
        accion = request.POST.get("accion")

        if accion == "rechazar":
            vistaprevia_post.objects.all().delete()
            messages.info(request, "Vista previa rechazada")
            return redirect('demo_generacion_post_redes_sociales')
                
        # Si viene del formulario (enviar descripción)
        descripcion = request.POST.get('descripcion', '').strip()
        imagen = request.FILES.get('imagen')
       
        if url: #Si url de llamada al webhook de n8n, se envía la descripción y la imagen a n8n
            mensaje_error = None
            try:
                datos_para_webhook = {"descripcion": descripcion}
                if imagen:
                    #Guardo la imagen y la descripción en la base de datos para obtener la url
                    obj = vistaprevia_post.objects.create(
                        texto = "PENDIENTE", #Pongo este texto para que no renderice hasta que n8n envíe su respuesta con el texto que genere la IA
                        imagen=imagen
                    )
                    #Construyo url pública con ngrok. Imprescindible para que se pueda enviar a n8n una ip pública.
                    #Si se trata de enviar localhost, n8n no podrá acceder.
                    imagen_url = request.build_absolute_uri(obj.imagen.url)
                    datos_para_webhook["imagen_url"] = imagen_url
                #Envío con JSON
                result = requests.post(url, json=datos_para_webhook, timeout=5)
                status = result.status_code
                messages.success(request, "Solicitud enviada correctamente a n8n")
            except Exception as e:
                mensaje_error = str(e)
                messages.error(request, f"Error al enviar a n8n: {str(e)}")
                status = None
        else:
            status = None
            mensaje_error = "No hay webhook configurado para esta automatización."
            messages.error(request, "no hay webhook configurado para esta automatización.")

        data = result.json()
        vistaprevia_texto = data.get("texto",'')
        vistaprevia_imagen = imagen
        

        context = {
            'submitted': True,
            'status': status,
            'error': mensaje_error,
            'webhook_url': url,
            'vistaprevia_texto': vistaprevia_texto,
            'vistaprevia_imagen': vistaprevia_imagen,
            'automatizacion': automatizacion,
        }
        return render(request, 'demo_automatizacion_2.html', context)

    # GET y cualquier otro método renderiza el formulario vacío
    return render(request, 'demo_automatizacion_2.html', {'automatizacion': automatizacion})


###############################################################################################

#Vista encargada de simular la venta de la automatización "Generación automática de post para redes sociales - Telegram"   
@login_requerido
def compra_generacion_post_redes_sociales(request):

    if request.method == 'POST':
        usuario = request.user

        #Obtengo la automatización
        automatizacion = get_object_or_404(automatizaciones, nombre="Generación automática de post para redes sociales - Telegram")

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
            messages.success(request, "Automatización comprada correctamente.")
        except Exception as e:
            messages.error(request, f"Error al procesar la compra: {str(e)}")
            return redirect('catalogo')
    
    return redirect('catalogo')

####################################################################################
@login_requerido
def activa_generacion_post_redes_sociales(request):

    mensaje_error = None

    #Obtengo la automatización desde la base de datos
    automatizacion = get_object_or_404(automatizaciones, nombre="Generación automática de post para redes sociales - Telegram")
    url = automatizacion.url_webhook

    #Muestra formulario limpio al cargar la página por primera vez o al hacer refresh.
    if request.method == 'GET':
        vistaprevia_post.objects.all().delete()
        return render(request, 'demo_automatizacion_2.html', {'automatizacion': automatizacion, 'webhook_url': url})
   
    #Envía a n8n la descripción y la imagen (si el usuario ha subido alguna) para que n8n la procese y genere el post
    if request.method == 'POST':
        accion = request.POST.get("accion")

        if accion == "rechazar":
            vistaprevia_post.objects.all().delete()
            messages.info(request, "Vista previa rechazada")
            return redirect('demo_generacion_post_redes_sociales')
                
        # Si viene del formulario (enviar descripción)
        descripcion = request.POST.get('descripcion', '').strip()
        imagen = request.FILES.get('imagen')
       
        if url: #Si url de llamada al webhook de n8n, se envía la descripción y la imagen a n8n
            mensaje_error = None
            try:
                datos_para_webhook = {"descripcion": descripcion}
                if imagen:
                    #Guardo la imagen y la descripción en la base de datos para obtener la url
                    obj = vistaprevia_post.objects.create(
                        texto = "PENDIENTE", #Pongo este texto para que no renderice hasta que n8n envíe su respuesta con el texto que genere la IA
                        imagen=imagen
                    )
                    #Construyo url pública con ngrok. Imprescindible para que se pueda enviar a n8n una ip pública.
                    #Si se trata de enviar localhost, n8n no podrá acceder.
                    imagen_url = request.build_absolute_uri(obj.imagen.url)
                    datos_para_webhook["imagen_url"] = imagen_url
                #Envío con JSON
                result = requests.post(url, json=datos_para_webhook, timeout=5)
                status = result.status_code
                messages.success(request, "Solicitud enviada correctamente a n8n")
            except Exception as e:
                mensaje_error = str(e)
                messages.error(request, f"Error al enviar a n8n: {str(e)}")
                status = None
        else:
            status = None
            mensaje_error = "No hay webhook configurado para esta automatización."
            messages.error(request, "no hay webhook configurado para esta automatización.")

        data = result.json()
        vistaprevia_texto = data.get("texto",'')
        vistaprevia_imagen = imagen
        

        context = {
            'submitted': True,
            'status': status,
            'error': mensaje_error,
            'webhook_url': url,
            'vistaprevia_texto': vistaprevia_texto,
            'vistaprevia_imagen': vistaprevia_imagen,
            'automatizacion': automatizacion,
        }
        return render(request, 'demo_automatizacion_2.html', context)

    # GET y cualquier otro método renderiza el formulario vacío
    return render(request, 'demo_automatizacion_2.html', {'automatizacion': automatizacion})


###########################################################################################
#endpoint al que n8n va a enviar el texto y la imagen del post para que el usuario los acepte / rechace.
@csrf_exempt
def recibir_vistaprevia_post(request):

    if request.method == "POST":

        texto = request.POST.get("texto")
        imagen = request.FILES.get("imagen")

        if imagen:
            #Si el nombre de la imagen no tiene extensión, se la pongo para que telegram no tenga problemas al postear
            extension = imagen.name.split('.')[-1] if '.' in imagen.name else 'jpg'
            imagen.name = f"post.{extension}"
            vistaprevia = vistaprevia_post.objects.create(texto=texto or "", imagen=imagen)

        else:
            #No llega imagen porque la subió el usuario así es que actualizo la vistaprevia existente en base de datos
            vistaprevia = vistaprevia_post.objects.order_by("-id").first()
            if vistaprevia:
                vistaprevia.texto = texto
                vistaprevia.save()
            else:
                vistaprevia = vistaprevia_post.objects.create(texto=texto or "", imagen=None)

        respuesta = {
            "status": "ok",
            "texto_recibido": texto,
            "imagen": vistaprevia.imagen.name if vistaprevia.imagen else None,
        }

        return JsonResponse(respuesta)

#####################################################################
#API para consultar si ya existe una vista previa y si es así, mostrarla en demo_automatizacion_2.html

@csrf_exempt
def api_obtener_vistaprevia(request):
    #Obtiene el último objeto de vistaprevia_post de la base de datos
    ultima_vistaprevia = vistaprevia_post.objects.order_by("-id").first()
    existe =False
    
    #if ultima_vistaprevia:
    if (ultima_vistaprevia and ultima_vistaprevia.texto and ultima_vistaprevia.texto != "PENDIENTE"):
        data = {
            "existe": True,
            "texto": ultima_vistaprevia.texto,
            "imagen": ultima_vistaprevia.imagen.name if ultima_vistaprevia.imagen else None,
            "id": ultima_vistaprevia.id,
        }
    else:
        data = {"existe": False}
    
    return JsonResponse(data)


########################################################################
#Vista que muestra la vista previa del post con opciones para confirmar o rechazar
def mostrar_vistaprevia_post(request):

    #Obtiene directamente el último registro de la base de datos (Vistaprevia_posts)
    vistaprevia = vistaprevia_post.objects.order_by("-id").first()

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "confirmar":
            #messages.success(request, "Post confirmado.")
            if vistaprevia:
                #Obtengo la automatización desde la base de datos
                automatizacion = get_object_or_404(automatizaciones, nombre="Generación automática de post para redes sociales - Telegram")
                #Obtengo la url del webhook encargado de postear
                webhook_postear_telegram = automatizacion.webhook.filter(
                    nombre="webhook_postear_telegram"
                ).first()

                if not webhook_postear_telegram:
                    raise Exception("Webhook 'webhook_postear' no encontrado")

                url_postear_telegram = webhook_postear_telegram.url

                imagen = vistaprevia.imagen
                datos_para_webhook = {'descripcion': vistaprevia.texto}
                if imagen:
                     #Construyo URL pública con ngrok.
                     #Para que funcione hay que arrancar ngrok http 8000
                    imagen_url = request.build_absolute_uri(vistaprevia.imagen.url)
                    data = {
                        "imagen_url": request.build_absolute_uri(vistaprevia.imagen.url),
                        "descripcion": vistaprevia.texto
                    }

                    try:
                        resultado = requests.post(url_postear_telegram, json=data, timeout=5)
                        resultado.raise_for_status()  # detecta errores HTTP
                        messages.success(request, "Post confirmado y enviado a n8n")
                    except requests.exceptions.RequestException as e:
                        messages.error(request, f"Error enviando a n8n: {e}")

        elif accion == "rechazar":
            if vistaprevia:
                vistaprevia.delete()
            messages.warning(request, "Post rechazado.")

        #return redirect("mostrar_vistaprevia_post")
        return redirect("demo_generacion_post_redes_sociales")

    context = {
        "vistaprevia": vistaprevia
    }

    return render(request, "demo_automatizacion_2.html", context)