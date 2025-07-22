# app/main.py
# Punto de entrada principal de la aplicación FastAPI

from fastapi import FastAPI
from app.api.v1 import endpoints

# Crear la instancia principal de la aplicación FastAPI
app = FastAPI()

# Incluir las rutas definidas en endpoints
app.include_router(endpoints.router) 