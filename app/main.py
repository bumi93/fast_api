# app/main.py
# Punto de entrada principal de la aplicación FastAPI

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1 import endpoints

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando aplicación...")
    refresh_interval = 90  # 1.5 minutos
    tasks = []
    try:
        # Lanza la tarea de refresco solo si el driver está activo
        if "driver" in endpoints.active_drivers:
            logger.info(f"Creando tarea de refresco para 'driver' con intervalo de {refresh_interval} segundos")
            tasks.append(asyncio.create_task(endpoints.refresh_driver_periodically("driver", refresh_interval)))
        if "driver_m" in endpoints.active_drivers:
            logger.info(f"Creando tarea de refresco para 'driver_m' con intervalo de {refresh_interval} segundos")
            tasks.append(asyncio.create_task(endpoints.refresh_driver_periodically("driver_m", refresh_interval)))
        yield
    finally:
        logger.info("Cerrando aplicación...")
        for task in tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        for driver_name, driver in endpoints.active_drivers.items():
            try:
                driver.quit()
                logger.info(f"Driver {driver_name} cerrado exitosamente")
            except Exception as e:
                logger.error(f"Error al cerrar driver {driver_name}: {str(e)}")

app = FastAPI(
    title="Web Scraping API",
    description="API para web scraping usando FastAPI y Selenium",
    version="1.0.0",
    lifespan=lifespan
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Incluir el router principal con prefijo /api/v1
app.include_router(endpoints.router, prefix="/api/v1")

# Incluir el endpoint de upload directamente (sin prefijo)
from app.api.v1.upload_endpoints import router as upload_router
app.include_router(upload_router) 