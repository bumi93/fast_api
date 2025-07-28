# app/data_management/__init__.py
"""
Paquete para manejo de datos y procesamiento de archivos CSV descargados de Ariba

Este paquete contiene tres módulos principales:

1. FileProcessor: Para cargar y obtener información de archivos CSV
2. DataValidator: Para validar la calidad y estructura de los datos
3. DataTransformer: Para limpiar y transformar los datos

Autor: Tu Nombre
Versión: 1.0.0
"""

# Importar las clases principales de cada módulo
from .file_processor import FileProcessor
from .data_validator import DataValidator
from .data_transformer import DataTransformer

# Lista de todas las clases que se pueden importar desde este paquete
__all__ = [
    'FileProcessor',    # Clase para procesar archivos CSV
    'DataValidator',    # Clase para validar datos
    'DataTransformer'   # Clase para transformar y limpiar datos
] 