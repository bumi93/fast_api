# app/core/config.py
# Configuración principal de la aplicación usando Pydantic

from pydantic import BaseSettings

# Clase de configuración que puede leer variables de entorno
class Settings(BaseSettings):
    app_name: str = "Bots-Latam v2"  # Nombre de la aplicación
    debug: bool = True  # Modo debug

# Instancia global de configuración
settings = Settings() 