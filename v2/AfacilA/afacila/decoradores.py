from functools import wraps
from django.db import transaction
from django.shortcuts import redirect
from django.contrib import messages
from afacila.models import perfil_usuario, automatizaciones

def limite_ejecuciones_demo(nombre_automatizacion):
    def decorator(view_func):
        @wraps(view_func)
        @transaction.atomic
        def _wrapped_view(request, *args, **kwargs):

            try:
                automatizacion = automatizaciones.objects.get(nombre=nombre_automatizacion)
            except automatizaciones.DoesNotExist:
                messages.error(request, "Automatización no encontrada")
                return redirect('catalogo')

            perfil, _ = perfil_usuario.objects.get_or_create(
                user=request.user,
                automatizacion=automatizacion
            )

            if not perfil.puede_ejecutar():
                messages.error(
                    request,
                    f"Has alcanzado el límite de {perfil.limite_ejecuciones_demo} ejecuciones"
                )
                return redirect('catalogo')

            if not perfil.tiene_subscripcion_activa():
                perfil.ejecuciones_demo += 1
                perfil.save(update_fields=["ejecuciones_demo"])

            return view_func(request, *args, **kwargs)

        return _wrapped_view
    return decorator
