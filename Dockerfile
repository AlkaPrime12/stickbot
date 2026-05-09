FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Imagen única: en Railway (u otro orquestador) definí el comando por servicio.
# Panel web (por defecto):
CMD ["python", "run_web.py"]
# Bot Discord (mismo build, otra instancia con la misma DATABASE_URL):
# CMD ["python", "run_bot.py"]
