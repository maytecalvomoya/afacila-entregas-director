from django.contrib import admin
from .models import automatizaciones, plan_suscripcion, suscripciones, vistaprevia_post, webhook, perfil_usuario

#admin.site.register(usuarios)
admin.site.register(automatizaciones)
admin.site.register(plan_suscripcion)
admin.site.register(suscripciones)
admin.site.register(vistaprevia_post)
admin.site.register(webhook)
admin.site.register(perfil_usuario)