# app/crud/excel_migration.py
"""
CRUD para migración de Excel a tablas SQL reales

Este módulo maneja la creación de tablas SQL reales basadas en archivos Excel
y la inserción de datos en estas tablas.
"""

import pandas as pd
import logging
from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)

# ============================================================================
# Funciones de Migración Excel → SQL
# ============================================================================

def create_table_from_excel_data(engine, table_name: str, df: pd.DataFrame, 
                                column_types: Dict[str, str] = None) -> bool:
    """
    Crea una tabla SQL real basada en los datos de un DataFrame de Excel
    
    Args:
        engine: Motor de SQLAlchemy
        table_name: Nombre de la tabla a crear
        df: DataFrame con los datos de Excel
        column_types: Diccionario con tipos de datos personalizados para columnas
        
    Returns:
        bool: True si se creó exitosamente
    """
    try:
        # Limpiar nombre de tabla (solo letras, números y guiones bajos)
        table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
        if table_name[0].isdigit():
            table_name = 'table_' + table_name
        
        # Determinar tipos de datos para cada columna
        column_definitions = _infer_column_types(df, column_types)
        
        # Crear SQL CREATE TABLE
        create_sql = f"CREATE TABLE {table_name} ("
        create_sql += "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        
        for col_name, col_type in column_definitions.items():
            create_sql += f"{col_name} {col_type}, "
        
        create_sql = create_sql.rstrip(", ") + ")"
        
        # Ejecutar creación de tabla
        with engine.connect() as conn:
            conn.execute(text(create_sql))
            conn.commit()
        
        logger.info(f"Tabla creada exitosamente: {table_name}")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"Error creando tabla {table_name}: {str(e)}")
        return False

def insert_data_to_table(engine, table_name: str, df: pd.DataFrame, 
                        column_mapping: Dict[str, str] = None) -> Tuple[int, int, List[str]]:
    """
    Inserta datos de Excel en una tabla SQL
    
    Args:
        engine: Motor de SQLAlchemy
        table_name: Nombre de la tabla destino
        df: DataFrame con los datos
        column_mapping: Mapeo de columnas (columna_excel -> columna_sql)
        
    Returns:
        Tuple[int, int, List[str]]: (insertados, omitidos, errores)
    """
    try:
        # Aplicar mapeo de columnas si se proporciona
        if column_mapping:
            df_mapped = df.rename(columns=column_mapping)
        else:
            df_mapped = df
        
        # Limpiar datos
        df_clean = _clean_dataframe(df_mapped)
        
        # Insertar datos
        inserted_count = 0
        skipped_count = 0
        errors = []
        
        with engine.connect() as conn:
            for index, row in df_clean.iterrows():
                try:
                    # Preparar datos para inserción
                    row_data = row.to_dict()
                    
                    # Eliminar valores NaN
                    row_data = {k: v for k, v in row_data.items() 
                               if pd.notna(v) and v != ''}
                    
                    if not row_data:
                        skipped_count += 1
                        continue
                    
                    # Crear SQL INSERT
                    columns = list(row_data.keys())
                    values = list(row_data.values())
                    placeholders = ', '.join(['?' for _ in values])
                    
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    
                    conn.execute(text(insert_sql), values)
                    inserted_count += 1
                    
                except Exception as e:
                    skipped_count += 1
                    errors.append(f"Fila {index + 1}: {str(e)}")
                    if len(errors) > 10:  # Limitar número de errores
                        break
            
            conn.commit()
        
        logger.info(f"Datos insertados en {table_name}: {inserted_count} exitosos, {skipped_count} omitidos")
        return inserted_count, skipped_count, errors
        
    except SQLAlchemyError as e:
        logger.error(f"Error insertando datos en {table_name}: {str(e)}")
        return 0, len(df), [f"Error general: {str(e)}"]

def get_existing_tables(engine) -> List[str]:
    """
    Obtiene lista de tablas existentes en la base de datos
    
    Args:
        engine: Motor de SQLAlchemy
        
    Returns:
        List[str]: Lista de nombres de tablas
    """
    try:
        inspector = inspect(engine)
        return inspector.get_table_names()
    except Exception as e:
        logger.error(f"Error obteniendo tablas: {str(e)}")
        return []

def get_table_columns(engine, table_name: str) -> List[str]:
    """
    Obtiene las columnas de una tabla específica
    
    Args:
        engine: Motor de SQLAlchemy
        table_name: Nombre de la tabla
        
    Returns:
        List[str]: Lista de nombres de columnas
    """
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        return [col['name'] for col in columns if col['name'] != 'id']
    except Exception as e:
        logger.error(f"Error obteniendo columnas de {table_name}: {str(e)}")
        return []

# ============================================================================
# Funciones Auxiliares
# ============================================================================

def _infer_column_types(df: pd.DataFrame, custom_types: Dict[str, str] = None) -> Dict[str, str]:
    """
    Infiere los tipos de datos SQL basándose en los datos del DataFrame
    
    Args:
        df: DataFrame con los datos
        custom_types: Tipos personalizados para columnas específicas
        
    Returns:
        Dict[str, str]: Mapeo columna -> tipo SQL
    """
    column_types = {}
    
    for column in df.columns:
        # Limpiar nombre de columna
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', str(column))
        if clean_name[0].isdigit():
            clean_name = 'col_' + clean_name
        
        # Usar tipo personalizado si se especifica
        if custom_types and column in custom_types:
            column_types[clean_name] = custom_types[column]
            continue
        
        # Inferir tipo basándose en los datos
        sample_data = df[column].dropna().head(100)
        
        if sample_data.empty:
            column_types[clean_name] = 'TEXT'
        elif df[column].dtype == 'object':
            # Verificar si son fechas
            try:
                pd.to_datetime(sample_data)
                column_types[clean_name] = 'DATE'
            except:
                # Verificar si son booleanos
                if sample_data.isin([True, False, 'True', 'False', 1, 0]).all():
                    column_types[clean_name] = 'BOOLEAN'
                else:
                    column_types[clean_name] = 'TEXT'
        elif df[column].dtype in ['int64', 'int32']:
            column_types[clean_name] = 'INTEGER'
        elif df[column].dtype in ['float64', 'float32']:
            column_types[clean_name] = 'REAL'
        else:
            column_types[clean_name] = 'TEXT'
    
    return column_types

def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia el DataFrame para inserción en SQL
    
    Args:
        df: DataFrame original
        
    Returns:
        pd.DataFrame: DataFrame limpio
    """
    # Limpiar nombres de columnas
    df.columns = [re.sub(r'[^a-zA-Z0-9_]', '_', str(col)) for col in df.columns]
    
    # Asegurar que los nombres empiecen con letra
    for i, col in enumerate(df.columns):
        if col[0].isdigit():
            df.columns.values[i] = 'col_' + col
    
    # Eliminar filas completamente vacías
    df = df.dropna(how='all')
    
    # Convertir fechas
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_datetime(df[col], errors='ignore')
            except:
                pass
    
    return df

def validate_table_name(table_name: str) -> bool:
    """
    Valida que el nombre de tabla sea válido para SQL
    
    Args:
        table_name: Nombre de la tabla
        
    Returns:
        bool: True si es válido
    """
    # Verificar que solo contenga caracteres válidos
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        return False
    
    # Verificar que no sea una palabra reservada
    reserved_words = ['SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 
                     'CREATE', 'DROP', 'TABLE', 'INDEX', 'PRIMARY', 'FOREIGN', 'KEY']
    
    if table_name.upper() in reserved_words:
        return False
    
    return True 