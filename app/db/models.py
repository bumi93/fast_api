# app/db/models.py
"""
Modelos de base de datos para la API

Este archivo contiene los modelos SQLAlchemy para todas las tablas:
- Usuarios (autenticación y 2FA)
- Feriados (datos estáticos)
- Diccionario Catálogo Empresa (datos estáticos)

Autor: Tu Nombre
Versión: 1.0.0
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# ============================================================================
# Modelo de Usuarios (Autenticación y 2FA)
# ============================================================================

class UserDB(Base):
    """
    Modelo de usuario para la base de datos
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)  # Contraseña hasheada
    totp_secret = Column(String(32), nullable=True)  # Secreto para 2FA
    role = Column(String(20), default="user")  # Rol del usuario (user, admin)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================================================
# Modelos de Datos Estáticos
# ============================================================================

class Feriado(Base):
    """
    Tabla de feriados por país
    """
    __tablename__ = "feriados"
    
    id = Column(Integer, primary_key=True, index=True)
    pais = Column(String(100), nullable=False, comment="País del feriado")
    feriado = Column(String(200), nullable=False, comment="Nombre del feriado")
    fecha = Column(Date, nullable=False, comment="Fecha del feriado")
    is_active = Column(Boolean, default=True, comment="Indica si el feriado está activo")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Fecha de creación")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Fecha de actualización")

class DiccionarioCatalogoEmpresa(Base):
    """
    Tabla de diccionario/catálogo de empresa
    """
    __tablename__ = "diccionario_catalogo_empresa"
    
    id = Column(Integer, primary_key=True, index=True)
    empresa = Column(String(200), nullable=False, comment="Nombre de la empresa")
    valor = Column(Text, nullable=False, comment="Valor del catálogo")
    is_active = Column(Boolean, default=True, comment="Indica si el registro está activo")
    created_at = Column(DateTime, default=datetime.utcnow, comment="Fecha de creación")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Fecha de actualización") 