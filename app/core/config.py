# app/core/config.py
# Configuración principal de la aplicación usando Pydantic

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

from pydantic_settings import BaseSettings

# Clase de configuración que puede leer variables de entorno
class Settings(BaseSettings):
    app_name: str = "Bots-Latam v2"  # Nombre de la aplicación
    debug: bool = True  # Modo debug

# Instancia global de configuración
settings = Settings() 