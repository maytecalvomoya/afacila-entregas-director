from django.contrib import admin
from django.urls import path

from afacila import vistas_automatizacion_2
from . import vistas_principal, vistas_automatizacion_1
from django.conf import settings
from django.conf.urls.static import static
from .vistas_automatizacion_1 import demo_campana_envio_email, compra_campana_envio_email
from .vistas_principal import mis_automatizaciones, activar_desactivar_suscripcion, vista_principal_1

#Establezco la función de vista que ha de ejecutar cuando el usuario visite la url.
urlpatterns = [
    path("admin/", admin.site.urls),
    path('', vistas_principal.vista_principal_1, name='inicio'),
    path('condiciones/', vistas_principal.condiciones, name='condiciones'),
    path('privacidad/', vistas_principal.privacidad, name='privacidad'),
    path('login/', vistas_principal.vista_login, name='login'),
    path('registro/', vistas_principal.vista_registro, name='registro'),
    path('catalogo/', vistas_principal.catalogo, name='catalogo'),
    path('mis_automatizaciones/', vistas_principal.mis_automatizaciones, name='mis_automatizaciones'),

    #Para parar las automatizaciones cuando las desactive el usuario.
    path('suscripcion/<int:id_suscripcion>/estado/', vistas_principal.estado_suscripcion),
    path('suscripcion/activar_desactivar_suscripcion/<int:id_suscripcion>/',vistas_principal.activar_desactivar_suscripcion,name='activar_desactivar_suscripcion'),
    
    #Vistas para la automatización 1
    path('demo_campana_envio_email/', vistas_automatizacion_1.demo_campana_envio_email, name='demo_campana_envio_email'),
    path('activa_campana_envio_email/', vistas_automatizacion_1.activa_campana_envio_email, name='activa_campana_envio_email'),
    path('compra_campana_envio_email/',vistas_automatizacion_1.compra_campana_envio_email, name='compra_campana_envio_email'),

    # Vistas para la automatización 2
    path('demo_generacion_post_redes_sociales/', vistas_automatizacion_2.demo_generacion_post_redes_sociales, name='demo_generacion_post_redes_sociales'),
    path('activa_generacion_post_redes_sociales/', vistas_automatizacion_2.activa_generacion_post_redes_sociales, name='activa_generacion_post_redes_sociales'),
    path('compra_generacion_post_redes_sociales/',vistas_automatizacion_2.compra_generacion_post_redes_sociales, name='compra_generacion_post_redes_sociales'),
    
    path("api/vistaprevia-post/", vistas_automatizacion_2.recibir_vistaprevia_post, name="vistaprevia_post"),
    path("api/obtener-vistaprevia/", vistas_automatizacion_2.api_obtener_vistaprevia, name="obtener_vistaprevia"),
    path("vistaprevia-post/", vistas_automatizacion_2.mostrar_vistaprevia_post, name="mostrar_vistaprevia_post"),

    # Vistas para la automatización 3
    #path('demo_monitor_precios/', vistas_automatizacion_3.demo_monitor_precios, name='demo_monitor_precios'),
    #path('activa_monitor_precios/', vistas_automatizacion_3.activa_monitor_precios, name='activa_monitor_precios'),
    #path('compra_monitor_precios/',vistas_automatizacion_3.compra_monitor_precios, name='compra_monitor_precios'),

    # Vistas para la automatización 4
    #path('activa_resumen_noticias/', vistas_automatizacion_4.activa_resumen_noticias, name='activa_resumen_noticias'),
    #path('demo_resumen_noticias/', vistas_automatizacion_4.demo_resumen_noticias, name='demo_resumen_noticias'),
    #path('compra_resumen_noticias/',vistas_automatizacion_4.compra_resumen_noticias, name='compra_resumen_noticias'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
