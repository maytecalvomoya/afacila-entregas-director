AFACILA – Automatizaciones con n8n

Requisitos

Antes de ejecutar el proyecto es necesario instalar: Docker Desktop, Python 3, Django y  ngrok

Ejecutar n8n con Docker Abrir una terminal en la carpeta del proyecto y ejecutar: docker compose up -d Esto iniciará el contenedor de n8n. Una vez iniciado, abrir en el navegador: http://localhost:5678

Importar las automatizaciones Las automatizaciones se encuentran en la carpeta AUTOMATIZACIONES Para importarlas en n8n: Abrir la interfaz de n8n. Seleccionar Import workflow. Elegir el archivo JSON correspondiente.

Ejecutar el backend Django Crear un entorno virtual: python -m venv venv Activar el entorno virtual. En Windows: venv\Scripts\activate En Linux o Mac: source venv/bin/activate Instalar las dependencias del proyecto: pip install -r requirements.txt Ejecutar el servidor Django: python manage.py runserver El backend estará disponible en: http://127.0.0.1:8000

Estructura del repositorio docker-compose.yml → configuración del contenedor de n8n requirements.txt → dependencias del backend Django AUTOMATIZACIONES → workflows exportados de n8n
