AFACILA – Automatizaciones con n8n

Requisitos

Antes de ejecutar el proyecto es necesario tener instalado:

- Docker Desktop
- Windows Subsystem for Linux 2 con Ubuntu 22.04
- Python 3
- Django
- ngrok

Instalación del backend (Django):
- Crear un entorno virtual: python -m venv venv y activarlo: venv\Scripts\activate
- Instalar las dependencias del proyecto: pip install -r requirements.txt
- Ejecutar el servidor Django: python manage.py runserver 0.0.0.0:8000. Esto es así por ngrok. El backend estará disponible en: https://unspreading-brock-nonobsessively.ngrok-free.dev/ (esto es así para permitir el acceso externo mediante ngrok).

Exposición del backend con ngrok:
- Descargar ngrok desde su web oficial e instalarlo
- Registrarse en ngrok para y obtener el authtoken.
- Configurar el token: Abrir consola en C:\ngrok y ejecutar: ngrok config add-authtoken TOKEN
- Ejecutar el tunel: ngrok http 8000
- Acceder al backend mediante la dirección https://unspreading-brock-nonobsessively.ngrok-free.dev/
- Durante todo el proceso, ngrok debe estar corriendo en una consola para exponer el backend a internet.

Instalación de Docker Desktop
- Habilitar virtualización en BIOS/UEFI
- Activar la característica de windows: dism.exe /online/enable-feature /featurename:VirtualMachinePlatform /all /norestart. Reiniciar el equipo.
- instalar WSL (distro de linux en windows) con wsl --install
- Verificar que la distro está en WSL2 con wsl -list -verbose. Si aparece la versión 1 hay que convertirla a 2 con wsl -set-version Ubuntu-22.04 2
- Durante la instalación de Docker Desktop marcar "Use WSDL 2 instead of Hyper-V".
- Activar integración con WSL en Docker Desktop: Abrir Docker Desktop > Settings > General. Ir a Resources > WSDL Integration y activar la distro Ubuntu. Aplicar cambios y reiniciar Docker Desktop.
- Verificar la instalación: docker --version y docker run hello-world (Esto iniciará el contenedor de n8n definido en docker-compose.yml)

Ejecutar n8n con Docker: 
- Abrir terminal en la carpeta del proyecto y ejecutar: docker compose up -d Esto iniciará el contenedor de n8n. El fichero docker-compose.yml está dentro de la carpeta del proyecto AfacilA.
- Acceder a la interfaz: http://localhost:5678

Importar las automatizaciones:
- Acceder a n8n en localhost:5678
- Ir a Import workflow y seleccionar los archivos JSON que hay en la carpeta AUTOMATIZACIONES.

Estructura del repositorio docker-compose.yml → configuración del contenedor de n8n requirements.txt → dependencias del backend Django AUTOMATIZACIONES → workflows exportados de n8n
