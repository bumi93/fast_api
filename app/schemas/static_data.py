# app/schemas/static_data.py
"""
Esquemas Pydantic para datos estáticos de la API

Este archivo contiene los esquemas de validación y serialización
para las tablas de referencia que no cambian frecuentemente.

Autor: Tu Nombre
Versión: 1.0.0
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

# ============================================================================
# Esquemas para Feriados
# ============================================================================

class FeriadoBase(BaseModel):
    """Esquema base para feriados"""
    pais: str = Field(..., description="País del feriado", max_length=100)
    feriado: str = Field(..., description="Nombre del feriado", max_length=200)
    fecha: date = Field(..., description="Fecha del feriado")
    is_active: bool = Field(True, description="Indica si el feriado está activo")

class FeriadoCreate(FeriadoBase):
    """Esquema para crear un nuevo feriado"""
    pass

class FeriadoUpdate(BaseModel):
    """Esquema para actualizar un feriado"""
    pais: Optional[str] = Field(None, description="País del feriado", max_length=100)
    feriado: Optional[str] = Field(None, description="Nombre del feriado", max_length=200)
    fecha: Optional[date] = Field(None, description="Fecha del feriado")
    is_active: Optional[bool] = Field(None, description="Indica si el feriado está activo")

class Feriado(FeriadoBase):
    """Esquema completo para feriados"""
    id: int = Field(..., description="ID único del feriado")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")
    
    class Config:
        from_attributes = True

# ============================================================================
# Esquemas para Diccionario Catálogo Empresa
# ============================================================================

class DiccionarioCatalogoEmpresaBase(BaseModel):
    """Esquema base para diccionario catálogo empresa"""
    empresa: str = Field(..., description="Nombre de la empresa", max_length=200)
    valor: str = Field(..., description="Valor del catálogo")
    is_active: bool = Field(True, description="Indica si el registro está activo")

class DiccionarioCatalogoEmpresaCreate(DiccionarioCatalogoEmpresaBase):
    """Esquema para crear un nuevo registro de diccionario catálogo empresa"""
    pass

class DiccionarioCatalogoEmpresaUpdate(BaseModel):
    """Esquema para actualizar un registro de diccionario catálogo empresa"""
    empresa: Optional[str] = Field(None, description="Nombre de la empresa", max_length=200)
    valor: Optional[str] = Field(None, description="Valor del catálogo")
    is_active: Optional[bool] = Field(None, description="Indica si el registro está activo")

class DiccionarioCatalogoEmpresa(DiccionarioCatalogoEmpresaBase):
    """Esquema completo para diccionario catálogo empresa"""
    id: int = Field(..., description="ID único del registro")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")
    
    class Config:
        from_attributes = True 