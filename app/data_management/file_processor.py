# app/data_management/file_processor.py
"""
Módulo para procesar archivos CSV descargados de Ariba

Este módulo proporciona funcionalidades para:
- Listar archivos CSV disponibles en una carpeta
- Cargar archivos CSV con diferentes encodings
- Obtener información detallada de archivos (tamaño, filas, columnas)
- Filtrar archivos por fecha de modificación
- Procesar múltiples archivos de forma eficiente

Autor: Tu Nombre
Versión: 1.0.0
"""

import os
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
import logging

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

class FileProcessor:
    """
    Clase para procesar archivos CSV descargados de Ariba
    
    Esta clase proporciona métodos para:
    - Explorar archivos CSV en una carpeta específica
    - Cargar archivos con manejo automático de encodings
    - Obtener metadatos de archivos (tamaño, fecha, estructura)
    - Filtrar archivos por diferentes criterios
    
    Ejemplo de uso:
        processor = FileProcessor("downloads/")
        files = processor.get_available_files()
        df = processor.load_csv_file("archivo.csv")
    """
    
    def __init__(self, download_path: str):
        """
        Inicializa el procesador de archivos
        
        Args:
            download_path: Ruta donde están los archivos descargados
                         (ejemplo: "downloads/" o "C:/MiCarpeta/")
        
        Ejemplo:
            processor = FileProcessor("downloads/")
        """
        # Guardar la ruta donde están los archivos CSV
        self.download_path = download_path
        
        # Lista para rastrear archivos que ya han sido procesados
        self.processed_files = []
        
        logger.info(f"FileProcessor inicializado con ruta: {download_path}")
        
    def get_available_files(self) -> List[str]:
        """
        Obtiene la lista de archivos CSV disponibles en la carpeta de descargas
        
        Este método:
        1. Verifica que la carpeta existe
        2. Busca todos los archivos con extensión .csv
        3. Retorna una lista con los nombres de archivos encontrados
        
        Returns:
            Lista de nombres de archivos CSV (ejemplo: ["archivo1.csv", "archivo2.csv"])
            
        Ejemplo:
            files = processor.get_available_files()
            print(f"Archivos encontrados: {files}")
        """
        try:
            # Verificar que la carpeta de descargas existe
            if not os.path.exists(self.download_path):
                logger.warning(f"La carpeta {self.download_path} no existe")
                return []
                
            # Buscar todos los archivos CSV en la carpeta
            csv_files = []
            for filename in os.listdir(self.download_path):
                # Solo incluir archivos que terminen en .csv
                if filename.endswith('.csv'):
                    csv_files.append(filename)
                    
            logger.info(f"Encontrados {len(csv_files)} archivos CSV en {self.download_path}")
            return csv_files
            
        except Exception as e:
            logger.error(f"Error al obtener archivos disponibles: {str(e)}")
            return []
    
    def load_csv_file(self, filename: str) -> Optional[pd.DataFrame]:
        """
        Carga un archivo CSV en un DataFrame de pandas
        
        Este método:
        1. Construye la ruta completa del archivo
        2. Verifica que el archivo existe
        3. Intenta cargar el archivo con diferentes encodings (utf-8, latin1, cp1252)
        4. Retorna un DataFrame de pandas con los datos
        
        Args:
            filename: Nombre del archivo CSV (ejemplo: "archivo.csv")
            
        Returns:
            DataFrame de pandas con los datos del archivo, o None si hay error
            
        Ejemplo:
            df = processor.load_csv_file("Backlog COMPRAS - LATAM - PR's.csv")
            if df is not None:
                print(f"Archivo cargado con {len(df)} filas y {len(df.columns)} columnas")
        """
        try:
            # Construir la ruta completa del archivo
            file_path = os.path.join(self.download_path, filename)
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                logger.error(f"El archivo {file_path} no existe")
                return None
                
            # Intentar cargar el archivo con diferentes encodings
            # Esto es necesario porque algunos archivos CSV pueden tener caracteres especiales
            encodings = ['utf-8', 'latin1', 'cp1252']
            for encoding in encodings:
                try:
                    # Cargar el archivo CSV en un DataFrame de pandas
                    df = pd.read_csv(file_path, encoding=encoding)
                    logger.info(f"Archivo {filename} cargado exitosamente con encoding {encoding}")
                    return df
                except UnicodeDecodeError:
                    # Si este encoding no funciona, probar el siguiente
                    continue
                    
            logger.error(f"No se pudo cargar el archivo {filename} con ningún encoding")
            return None
            
        except Exception as e:
            logger.error(f"Error al cargar archivo {filename}: {str(e)}")
            return None
    
    def get_file_info(self, filename: str) -> Dict:
        """
        Obtiene información detallada de un archivo
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Diccionario con información del archivo
        """
        try:
            file_path = os.path.join(self.download_path, filename)
            if not os.path.exists(file_path):
                return {"error": "Archivo no encontrado"}
                
            stat = os.stat(file_path)
            file_size = stat.st_size
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Intentar obtener información del DataFrame
            df = self.load_csv_file(filename)
            if df is not None:
                return {
                    "filename": filename,
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "modified_date": modified_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns)
                }
            else:
                return {
                    "filename": filename,
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "modified_date": modified_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "error": "No se pudo cargar el DataFrame"
                }
                
        except Exception as e:
            logger.error(f"Error al obtener información del archivo {filename}: {str(e)}")
            return {"error": str(e)}
    
    def process_all_files(self) -> Dict:
        """
        Procesa todos los archivos CSV disponibles
        
        Returns:
            Diccionario con información de todos los archivos procesados
        """
        try:
            files = self.get_available_files()
            if not files:
                return {"message": "No se encontraron archivos CSV para procesar"}
                
            results = {}
            for filename in files:
                logger.info(f"Procesando archivo: {filename}")
                file_info = self.get_file_info(filename)
                results[filename] = file_info
                
            logger.info(f"Procesamiento completado. {len(results)} archivos procesados")
            return results
            
        except Exception as e:
            logger.error(f"Error en procesamiento de archivos: {str(e)}")
            return {"error": str(e)}
    
    def filter_files_by_date(self, target_date: date = None) -> List[str]:
        """
        Filtra archivos por fecha de modificación
        
        Args:
            target_date: Fecha objetivo (por defecto hoy)
            
        Returns:
            Lista de archivos que coinciden con la fecha
        """
        try:
            if target_date is None:
                target_date = date.today()
                
            files = self.get_available_files()
            filtered_files = []
            
            for filename in files:
                file_path = os.path.join(self.download_path, filename)
                stat = os.stat(file_path)
                file_date = datetime.fromtimestamp(stat.st_mtime).date()
                
                if file_date == target_date:
                    filtered_files.append(filename)
                    
            logger.info(f"Encontrados {len(filtered_files)} archivos de la fecha {target_date}")
            return filtered_files
            
        except Exception as e:
            logger.error(f"Error al filtrar archivos por fecha: {str(e)}")
            return [] 