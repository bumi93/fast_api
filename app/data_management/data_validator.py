# app/data_management/data_validator.py
"""
Módulo para validar datos en archivos CSV descargados de Ariba

Este módulo proporciona funcionalidades para:
- Validar la estructura y calidad de datos en archivos CSV
- Verificar completitud de datos (valores faltantes)
- Detectar duplicados y inconsistencias
- Validaciones específicas por tipo de archivo (PR, Catálogo, Legal)
- Generar reportes de validación con estadísticas

Autor: Tu Nombre
Versión: 1.0.0
"""

import pandas as pd
from typing import List, Dict, Optional, Tuple
import logging

# Configurar logger para este módulo
logger = logging.getLogger(__name__)

class DataValidator:
    """
    Clase para validar datos en archivos CSV
    
    Esta clase proporciona métodos para:
    - Validar la estructura de DataFrames
    - Verificar la calidad de los datos
    - Detectar problemas comunes en archivos CSV
    - Generar reportes de validación
    
    Ejemplo de uso:
        validator = DataValidator()
        results = validator.validate_dataframe(df, "archivo.csv")
        summary = validator.get_validation_summary(results)
    """
    
    def __init__(self):
        """
        Inicializa el validador de datos
        
        Este constructor:
        1. Crea un diccionario para almacenar reglas de validación personalizadas
        2. Crea un diccionario para almacenar resultados de validaciones previas
        
        Ejemplo:
            validator = DataValidator()
        """
        # Diccionario para almacenar reglas de validación personalizadas
        self.validation_rules = {}
        
        # Diccionario para almacenar resultados de validaciones previas
        self.validation_results = {}
        
        logger.info("DataValidator inicializado")
        
    def validate_dataframe(self, df: pd.DataFrame, filename: str) -> Dict:
        """
        Valida un DataFrame completo
        
        Args:
            df: DataFrame a validar
            filename: Nombre del archivo para referencia
            
        Returns:
            Diccionario con resultados de validación
        """
        try:
            results = {
                "filename": filename,
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "validations": {}
            }
            
            # Validaciones básicas
            results["validations"]["basic"] = self._validate_basic(df)
            
            # Validaciones de columnas
            results["validations"]["columns"] = self._validate_columns(df)
            
            # Validaciones de datos
            results["validations"]["data"] = self._validate_data_quality(df)
            
            # Validaciones específicas por tipo de archivo
            if "PR" in filename:
                results["validations"]["pr_specific"] = self._validate_pr_data(df)
            elif "CATALOG" in filename:
                results["validations"]["catalog_specific"] = self._validate_catalog_data(df)
            elif "LEGAL" in filename:
                results["validations"]["legal_specific"] = self._validate_legal_data(df)
                
            logger.info(f"Validación completada para {filename}")
            return results
            
        except Exception as e:
            logger.error(f"Error en validación de {filename}: {str(e)}")
            return {"error": str(e)}
    
    def _validate_basic(self, df: pd.DataFrame) -> Dict:
        """Validaciones básicas del DataFrame"""
        return {
            "has_data": len(df) > 0,
            "has_columns": len(df.columns) > 0,
            "is_empty": df.empty,
            "duplicate_rows": len(df[df.duplicated()]),
            "null_values_total": df.isnull().sum().sum()
        }
    
    def _validate_columns(self, df: pd.DataFrame) -> Dict:
        """Validaciones de columnas"""
        column_info = {}
        for col in df.columns:
            column_info[col] = {
                "data_type": str(df[col].dtype),
                "null_count": df[col].isnull().sum(),
                "unique_values": df[col].nunique(),
                "has_duplicates": df[col].duplicated().any()
            }
        
        return {
            "column_count": len(df.columns),
            "columns_info": column_info
        }
    
    def _validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """Validaciones de calidad de datos"""
        return {
            "completeness": (df.notnull().sum().sum() / (len(df) * len(df.columns))) * 100,
            "unique_ratio": df.nunique().sum() / (len(df) * len(df.columns)),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024)
        }
    
    def _validate_pr_data(self, df: pd.DataFrame) -> Dict:
        """Validaciones específicas para archivos de PR"""
        pr_validations = {}
        
        # Buscar columnas comunes en archivos PR
        expected_columns = ["PR", "Purchase Requisition", "Requisition", "ID", "Number"]
        found_columns = [col for col in df.columns if any(expected in col.upper() for expected in expected_columns)]
        
        pr_validations["has_pr_columns"] = len(found_columns) > 0
        pr_validations["pr_columns_found"] = found_columns
        
        return pr_validations
    
    def _validate_catalog_data(self, df: pd.DataFrame) -> Dict:
        """Validaciones específicas para archivos de catálogo"""
        catalog_validations = {}
        
        # Buscar columnas comunes en catálogos
        expected_columns = ["Material", "Item", "Product", "Code", "Description"]
        found_columns = [col for col in df.columns if any(expected in col.upper() for expected in expected_columns)]
        
        catalog_validations["has_catalog_columns"] = len(found_columns) > 0
        catalog_validations["catalog_columns_found"] = found_columns
        
        return catalog_validations
    
    def _validate_legal_data(self, df: pd.DataFrame) -> Dict:
        """Validaciones específicas para archivos legales"""
        legal_validations = {}
        
        # Buscar columnas comunes en archivos legales
        expected_columns = ["Legal", "Status", "Approval", "Review", "Compliance"]
        found_columns = [col for col in df.columns if any(expected in col.upper() for expected in expected_columns)]
        
        legal_validations["has_legal_columns"] = len(found_columns) > 0
        legal_validations["legal_columns_found"] = found_columns
        
        return legal_validations
    
    def validate_multiple_files(self, file_processor, filenames: List[str]) -> Dict:
        """
        Valida múltiples archivos
        
        Args:
            file_processor: Instancia de FileProcessor
            filenames: Lista de nombres de archivos a validar
            
        Returns:
            Diccionario con resultados de validación de todos los archivos
        """
        try:
            all_results = {}
            
            for filename in filenames:
                logger.info(f"Validando archivo: {filename}")
                df = file_processor.load_csv_file(filename)
                
                if df is not None:
                    validation_result = self.validate_dataframe(df, filename)
                    all_results[filename] = validation_result
                else:
                    all_results[filename] = {"error": "No se pudo cargar el archivo"}
                    
            logger.info(f"Validación completada para {len(filenames)} archivos")
            return all_results
            
        except Exception as e:
            logger.error(f"Error en validación múltiple: {str(e)}")
            return {"error": str(e)}
    
    def get_validation_summary(self, validation_results: Dict) -> Dict:
        """
        Genera un resumen de los resultados de validación
        
        Args:
            validation_results: Resultados de validación
            
        Returns:
            Resumen de validación
        """
        try:
            summary = {
                "total_files": len(validation_results),
                "files_with_errors": 0,
                "files_with_warnings": 0,
                "total_rows": 0,
                "total_columns": 0,
                "average_completeness": 0
            }
            
            completeness_scores = []
            
            for filename, result in validation_results.items():
                if "error" in result:
                    summary["files_with_errors"] += 1
                    continue
                    
                if "validations" in result:
                    summary["total_rows"] += result.get("total_rows", 0)
                    summary["total_columns"] += result.get("total_columns", 0)
                    
                    # Verificar completitud
                    if "data" in result["validations"]:
                        completeness = result["validations"]["data"].get("completeness", 0)
                        completeness_scores.append(completeness)
                        
                        if completeness < 90:  # Menos del 90% de completitud
                            summary["files_with_warnings"] += 1
            
            if completeness_scores:
                summary["average_completeness"] = sum(completeness_scores) / len(completeness_scores)
                
            return summary
            
        except Exception as e:
            logger.error(f"Error al generar resumen: {str(e)}")
            return {"error": str(e)} 