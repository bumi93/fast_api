# app/data_management/data_transformer.py
"""
Módulo para transformar y limpiar datos de archivos CSV descargados de Ariba

Este módulo proporciona funcionalidades para:
- Limpiar y estandarizar datos en archivos CSV
- Eliminar duplicados y valores faltantes
- Normalizar nombres de columnas
- Estandarizar formatos de fecha
- Aplicar limpiezas específicas por tipo de archivo
- Guardar datos limpios en nuevos archivos

Autor: Tu Nombre
Versión: 1.0.0
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
import logging
from datetime import datetime, date
import re
import os

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

class DataTransformer:
    """
    Clase para transformar y limpiar datos de archivos CSV
    
    Esta clase proporciona métodos para:
    - Limpiar DataFrames aplicando transformaciones estándar
    - Eliminar duplicados y manejar valores faltantes
    - Normalizar nombres de columnas y formatos de datos
    - Aplicar limpiezas específicas según el tipo de archivo
    - Guardar datos limpios en nuevos archivos
    
    Ejemplo de uso:
        transformer = DataTransformer()
        df_clean = transformer.clean_dataframe(df, "archivo.csv")
        summary = transformer.get_transformation_summary()
    """
    
    def __init__(self):
        """
        Inicializa el transformador de datos
        
        Este constructor:
        1. Crea una lista para rastrear las transformaciones aplicadas
        2. Crea un diccionario para almacenar reglas de limpieza personalizadas
        
        Ejemplo:
            transformer = DataTransformer()
        """
        # Lista para rastrear todas las transformaciones aplicadas
        self.transformations_applied = []
        
        # Diccionario para almacenar reglas de limpieza personalizadas
        self.cleaning_rules = {}
        
        logger.info("DataTransformer inicializado")
        
    def clean_dataframe(self, df: pd.DataFrame, filename: str) -> pd.DataFrame:
        """
        Limpia un DataFrame aplicando transformaciones básicas
        
        Args:
            df: DataFrame a limpiar
            filename: Nombre del archivo para referencia
            
        Returns:
            DataFrame limpio
        """
        try:
            logger.info(f"Iniciando limpieza de datos para {filename}")
            
            # Crear una copia para no modificar el original
            df_clean = df.copy()
            
            # Aplicar limpiezas básicas
            df_clean = self._remove_duplicates(df_clean)
            df_clean = self._clean_column_names(df_clean)
            df_clean = self._handle_missing_values(df_clean)
            df_clean = self._clean_string_columns(df_clean)
            df_clean = self._standardize_date_columns(df_clean)
            
            # Limpiezas específicas por tipo de archivo
            if "PR" in filename:
                df_clean = self._clean_pr_data(df_clean)
            elif "CATALOG" in filename:
                df_clean = self._clean_catalog_data(df_clean)
            elif "LEGAL" in filename:
                df_clean = self._clean_legal_data(df_clean)
                
            logger.info(f"Limpieza completada para {filename}. Filas: {len(df)} -> {len(df_clean)}")
            return df_clean
            
        except Exception as e:
            logger.error(f"Error en limpieza de {filename}: {str(e)}")
            return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Elimina filas duplicadas"""
        initial_rows = len(df)
        df_clean = df.drop_duplicates()
        removed_rows = initial_rows - len(df_clean)
        
        if removed_rows > 0:
            logger.info(f"Eliminadas {removed_rows} filas duplicadas")
            self.transformations_applied.append(f"Removed {removed_rows} duplicate rows")
            
        return df_clean
    
    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia nombres de columnas"""
        df_clean = df.copy()
        
        # Convertir a minúsculas y reemplazar espacios
        df_clean.columns = df_clean.columns.str.lower().str.replace(' ', '_').str.replace('-', '_')
        
        # Eliminar caracteres especiales
        df_clean.columns = df_clean.columns.str.replace(r'[^\w\s]', '', regex=True)
        
        # Eliminar espacios al inicio y final
        df_clean.columns = df_clean.columns.str.strip()
        
        self.transformations_applied.append("Cleaned column names")
        return df_clean
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Maneja valores faltantes"""
        df_clean = df.copy()
        
        # Para columnas numéricas, reemplazar NaN con 0
        numeric_columns = df_clean.select_dtypes(include=[np.number]).columns
        df_clean[numeric_columns] = df_clean[numeric_columns].fillna(0)
        
        # Para columnas de texto, reemplazar NaN con "N/A"
        text_columns = df_clean.select_dtypes(include=['object']).columns
        df_clean[text_columns] = df_clean[text_columns].fillna("N/A")
        
        self.transformations_applied.append("Handled missing values")
        return df_clean
    
    def _clean_string_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia columnas de texto"""
        df_clean = df.copy()
        
        # Aplicar limpieza a columnas de texto
        text_columns = df_clean.select_dtypes(include=['object']).columns
        
        for col in text_columns:
            # Eliminar espacios extra
            df_clean[col] = df_clean[col].astype(str).str.strip()
            
            # Convertir a título para consistencia
            df_clean[col] = df_clean[col].str.title()
            
            # Reemplazar múltiples espacios con uno solo
            df_clean[col] = df_clean[col].str.replace(r'\s+', ' ', regex=True)
        
        self.transformations_applied.append("Cleaned string columns")
        return df_clean
    
    def _standardize_date_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Estandariza columnas de fecha"""
        df_clean = df.copy()
        
        # Buscar columnas que podrían ser fechas
        date_keywords = ['date', 'fecha', 'created', 'modified', 'updated', 'time']
        potential_date_columns = []
        
        for col in df_clean.columns:
            if any(keyword in col.lower() for keyword in date_keywords):
                potential_date_columns.append(col)
        
        for col in potential_date_columns:
            try:
                # Intentar convertir a datetime
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                logger.info(f"Convertida columna {col} a datetime")
            except Exception:
                logger.warning(f"No se pudo convertir {col} a datetime")
        
        self.transformations_applied.append("Standardized date columns")
        return df_clean
    
    def _clean_pr_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpiezas específicas para datos de PR"""
        df_clean = df.copy()
        
        # Buscar columnas de PR
        pr_columns = [col for col in df_clean.columns if 'pr' in col.lower() or 'requisition' in col.lower()]
        
        for col in pr_columns:
            # Limpiar códigos de PR (eliminar espacios y caracteres especiales)
            df_clean[col] = df_clean[col].astype(str).str.replace(r'[^\w\s]', '', regex=True)
            df_clean[col] = df_clean[col].str.strip()
        
        self.transformations_applied.append("Cleaned PR-specific data")
        return df_clean
    
    def _clean_catalog_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpiezas específicas para datos de catálogo"""
        df_clean = df.copy()
        
        # Buscar columnas de material/código
        material_columns = [col for col in df_clean.columns if 'material' in col.lower() or 'code' in col.lower()]
        
        for col in material_columns:
            # Estandarizar códigos de material
            df_clean[col] = df_clean[col].astype(str).str.upper().str.strip()
        
        self.transformations_applied.append("Cleaned catalog-specific data")
        return df_clean
    
    def _clean_legal_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpiezas específicas para datos legales"""
        df_clean = df.copy()
        
        # Buscar columnas de estado
        status_columns = [col for col in df_clean.columns if 'status' in col.lower() or 'state' in col.lower()]
        
        for col in status_columns:
            # Estandarizar estados
            df_clean[col] = df_clean[col].astype(str).str.upper().str.strip()
        
        self.transformations_applied.append("Cleaned legal-specific data")
        return df_clean
    
    def transform_multiple_files(self, file_processor, filenames: List[str]) -> Dict:
        """
        Transforma múltiples archivos
        
        Args:
            file_processor: Instancia de FileProcessor
            filenames: Lista de nombres de archivos a transformar
            
        Returns:
            Diccionario con DataFrames transformados
        """
        try:
            transformed_data = {}
            
            for filename in filenames:
                logger.info(f"Transformando archivo: {filename}")
                df = file_processor.load_csv_file(filename)
                
                if df is not None:
                    df_clean = self.clean_dataframe(df, filename)
                    transformed_data[filename] = df_clean
                else:
                    logger.warning(f"No se pudo cargar {filename} para transformación")
                    
            logger.info(f"Transformación completada para {len(transformed_data)} archivos")
            return transformed_data
            
        except Exception as e:
            logger.error(f"Error en transformación múltiple: {str(e)}")
            return {"error": str(e)}
    
    def save_transformed_data(self, transformed_data: Dict, output_path: str) -> Dict:
        """
        Guarda los datos transformados
        
        Args:
            transformed_data: Diccionario con DataFrames transformados
            output_path: Ruta donde guardar los archivos
            
        Returns:
            Diccionario con información de archivos guardados
        """
        try:
            saved_files = {}
            
            for filename, df in transformed_data.items():
                if isinstance(df, pd.DataFrame):
                    # Crear nombre de archivo para datos limpios
                    clean_filename = f"clean_{filename}"
                    output_file = f"{output_path}/{clean_filename}"
                    
                    # Guardar como CSV
                    df.to_csv(output_file, index=False, encoding='utf-8')
                    
                    saved_files[filename] = {
                        "output_file": clean_filename,
                        "rows": len(df),
                        "columns": len(df.columns),
                        "file_size_mb": round(os.path.getsize(output_file) / (1024 * 1024), 2)
                    }
                    
                    logger.info(f"Archivo transformado guardado: {clean_filename}")
                    
            return saved_files
            
        except Exception as e:
            logger.error(f"Error al guardar datos transformados: {str(e)}")
            return {"error": str(e)}
    
    def get_transformation_summary(self) -> Dict:
        """
        Obtiene un resumen de las transformaciones aplicadas
        
        Returns:
            Resumen de transformaciones
        """
        return {
            "total_transformations": len(self.transformations_applied),
            "transformations_applied": self.transformations_applied
        } 