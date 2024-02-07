FROM python:3.9

# Instalar las dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql \
    && rm -rf /var/lib/apt/lists/*

# Copiar el código fuente al contenedor
WORKDIR /app
COPY . /app

# Instalar las dependencias de Python
RUN pip install -r requirements.txt

# Exponer el puerto que utiliza tu aplicación
EXPOSE 8080

# Comando para ejecutar tu aplicación
CMD ["python", "telegram.py"]
