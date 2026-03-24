from django.db import models
from django.contrib.auth.models import User
    
class automatizaciones(models.Model):

    nombre = models.CharField(max_length=150)
    disponible = models.BooleanField(default=True)
    version = models.CharField(max_length=50)
    url_webhook = models.URLField()
    url_demo_webhook = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    #Defino una propiedad para obtener el nombre de la vista de configuración asociada a la automatización.
    @property
    def nombre_vista(self):
        mapeo_demo = {
            "Campañas de email programadas": "activa_campana_envio_email",
            "Generación automática de post para redes sociales - Telegram": "activa_generacion_post_redes_sociales",
            "Monitor de precios de productos": "activa_monitor_precios",
            "Resumen automático de noticias": "activa_resumen_noticias",
        }
        return mapeo_demo.get(self.nombre)
    
class webhook(models.Model):
    automatizacion = models.ForeignKey(
        automatizaciones,
        on_delete=models.CASCADE,
        related_name="webhook"
    )
    nombre = models.CharField(max_length=255)
    url = models.URLField()

    def __str__(self):
        return f"{self.automatizacion.nombre} - {self.nombre}"
    
class plan_suscripcion(models.Model):
    TIPOS_SUSCRIPCION = [
        ('Mensual', 'Mensual'),
        ('Anual', 'Anual'),
    ]

    automatizacion = models.ForeignKey(automatizaciones, on_delete=models.CASCADE, related_name='plan')
    tipo_suscripcion = models.CharField(max_length=10, choices=TIPOS_SUSCRIPCION)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.automatizacion.nombre} - {self.tipo_suscripcion}"
    

class suscripciones(models.Model):
    automatizacion = models.ForeignKey(automatizaciones, on_delete=models.CASCADE, related_name='suscripciones')
    plan = models.ForeignKey(plan_suscripcion, on_delete=models.CASCADE,related_name='suscripciones')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suscripciones')
    activada = models.BooleanField(default=False)
    fecha_suscripcion = models.DateField(auto_now_add=True)
    fecha_caducidad = models.DateField()
    parametros = models.JSONField(blank=True, null=True)
    id_ejecucion_n8n = models.CharField(max_length=200, blank=True, null=True) #Guarda el identificador de la ejecución en n8n para poder desactivarla.

    def __str__(self):
        return f"{self.usuario} - {self.automatizacion}"

class vistaprevia_post(models.Model):
    '''Almacena las vistas previas de los post temporales desde n8n'''
    texto = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to='posts/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now = True)

    class Meta:
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Preview - {self.fecha_creacion}"

class perfil_usuario(models.Model):
    '''Estado del usuario para cada automatización'''

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    automatizacion = models.ForeignKey(automatizaciones, on_delete=models.CASCADE)

    ejecuciones_demo = models.IntegerField(default=0)
    limite_ejecuciones_demo = models.IntegerField(default=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'automatizacion'],
                name='unique_user_automatizacion'
            )
        ]

    def tiene_subscripcion_activa(self):
        return suscripciones.objects.filter(
            usuario=self.user,
            automatizacion=self.automatizacion,
            activada=True
        ).exists()

    def puede_ejecutar(self):
        if self.tiene_subscripcion_activa():
            return True
        return self.ejecuciones_demo < self.limite_ejecuciones_demo

