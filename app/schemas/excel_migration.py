# app/schemas/excel_migration.py
"""
Schemas para migración de Excel a tablas SQL reales

Este módulo define los modelos Pydantic para validar los datos
de entrada en la migración de Excel a SQL.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime

# ============================================================================
# Schemas para Creación de Tablas
# ============================================================================

class ColumnDefinition(BaseModel):
    """Definición de una columna para crear tabla SQL"""
    name: str = Field(..., description="Nombre de la columna")
    display_name: str = Field(..., description="Nombre para mostrar")
    data_type: str = Field(..., description="Tipo de dato SQL (TEXT, INTEGER, REAL, DATE, BOOLEAN)")
    required: bool = Field(default=False, description="Si la columna es obligatoria")
    description: Optional[str] = Field(None, description="Descripción de la columna")
    default_value: Optional[Any] = Field(None, description="Valor por defecto")
    
    @validator('data_type')
    def validate_data_type(cls, v):
        valid_types = ['TEXT', 'INTEGER', 'REAL', 'DATE', 'BOOLEAN']
        if v.upper() not in valid_types:
            raise ValueError(f'Tipo de dato debe ser uno de: {", ".join(valid_types)}')
        return v.upper()
    
    @validator('name')
    def validate_column_name(cls, v):
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError('Nombre de columna debe empezar con letra y contener solo letras, números y guiones bajos')
        return v

class CreateTableRequest(BaseModel):
    """Request para crear una nueva tabla SQL"""
    table_name: str = Field(..., description="Nombre de la tabla")
    display_name: str = Field(..., description="Nombre para mostrar")
    description: Optional[str] = Field(None, description="Descripción de la tabla")
    columns: List[ColumnDefinition] = Field(..., description="Lista de columnas")
    
    @validator('table_name')
    def validate_table_name(cls, v):
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', v):
            raise ValueError('Nombre de tabla debe empezar con letra y contener solo letras, números y guiones bajos')
        return v

# ============================================================================
# Schemas para Inserción de Datos
# ============================================================================

class DataInsertRequest(BaseModel):
    """Request para insertar datos en una tabla"""
    table_name: str = Field(..., description="Nombre de la tabla destino")
    column_mapping: Dict[str, str] = Field(..., description="Mapeo de columnas Excel -> SQL")
    data: List[Dict[str, Any]] = Field(..., description="Datos a insertar")
    create_new_table: bool = Field(default=False, description="Si debe crear nueva tabla")
    new_table_info: Optional[CreateTableRequest] = Field(None, description="Info para nueva tabla")

class DataInsertResponse(BaseModel):
    """Response de inserción de datos"""
    success: bool = Field(..., description="Si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    inserted_count: int = Field(..., description="Número de registros insertados")
    skipped_count: int = Field(..., description="Número de registros omitidos")
    total_count: int = Field(..., description="Total de registros procesados")
    errors: List[str] = Field(default=[], description="Lista de errores")
    table_created: bool = Field(default=False, description="Si se creó una nueva tabla")
    new_table_name: Optional[str] = Field(None, description="Nombre de la tabla creada")

# ============================================================================
# Schemas para Tablas Existentes
# ============================================================================

class TableInfo(BaseModel):
    """Información de una tabla existente"""
    name: str = Field(..., description="Nombre de la tabla")
    display_name: str = Field(..., description="Nombre para mostrar")
    description: Optional[str] = Field(None, description="Descripción")
    columns: List[str] = Field(..., description="Lista de columnas")
    row_count: Optional[int] = Field(None, description="Número de filas")
    created_at: Optional[datetime] = Field(None, description="Fecha de creación")

class TablesListResponse(BaseModel):
    """Response con lista de tablas disponibles"""
    success: bool = Field(..., description="Si la operación fue exitosa")
    tables: Dict[str, TableInfo] = Field(..., description="Diccionario de tablas")
    message: Optional[str] = Field(None, description="Mensaje adicional")

# ============================================================================
# Schemas para Preview de Datos
# ============================================================================

class PreviewData(BaseModel):
    """Datos de previsualización de Excel"""
    columns: List[str] = Field(..., description="Nombres de las columnas")
    rows: List[Dict[str, Any]] = Field(..., description="Primeras filas de datos")
    total_rows: int = Field(..., description="Total de filas en el archivo")
    file_info: Dict[str, Any] = Field(..., description="Información del archivo")

class PreviewResponse(BaseModel):
    """Response de previsualización"""
    success: bool = Field(..., description="Si la operación fue exitosa")
    data: Optional[PreviewData] = Field(None, description="Datos de previsualización")
    message: Optional[str] = Field(None, description="Mensaje de error si aplica")

# ============================================================================
# Schemas para Validación
# ============================================================================

class ValidationError(BaseModel):
    """Error de validación"""
    field: str = Field(..., description="Campo con error")
    message: str = Field(..., description="Mensaje de error")
    value: Optional[Any] = Field(None, description="Valor que causó el error")

class ValidationResponse(BaseModel):
    """Response de validación"""
    is_valid: bool = Field(..., description="Si los datos son válidos")
    errors: List[ValidationError] = Field(default=[], description="Lista de errores")
    warnings: List[str] = Field(default=[], description="Lista de advertencias") 