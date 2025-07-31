# app/db/models.py
"""
Modelos de base de datos para la API

Este archivo contiene los modelos SQLAlchemy para todas las tablas:
- Usuarios (autenticación y 2FA)
- Feriados (datos estáticos)
- Diccionario Catálogo Empresa (datos estáticos)
- Tablas Dinámicas (nuevas tablas creadas por el usuario)

Autor: Tu Nombre
Versión: 1.0.0
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, JSON
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


    """
    Datos de las tablas dinámicas (tabla genérica)
    
    Esta es una tabla genérica que almacena TODOS los datos de TODAS las tablas dinámicas.
    En lugar de crear una tabla física por cada tabla dinámica, usamos esta tabla
    que almacena los datos en formato JSON. Esto es más flexible y seguro.
    """
    __tablename__ = "dynamic_table_data"  # Nombre de la tabla en la base de datos
    
    # Identificador único del registro (clave primaria)
    id = Column(Integer, primary_key=True, index=True)
    
    # Nombre de la tabla dinámica a la que pertenece este dato
    # Se usa para filtrar datos por tabla
    table_name = Column(String(100), nullable=False, comment="Nombre de la tabla dinámica")
    
    # Datos de la fila en formato JSON
    # Ejemplo: {"nombre": "Laptop", "precio": 999.99, "categoria": "Electrónicos"}
    data = Column(JSON, nullable=False, comment="Datos de la fila en formato JSON")
    
    # ID del usuario que insertó estos datos
    # Se usa para auditoría y control de acceso
    created_by = Column(Integer, nullable=False, comment="ID del usuario que insertó los datos")
    
    # Indica si el registro está activo (soft delete)
    # En lugar de eliminar físicamente, se marca como inactivo
    is_active = Column(Boolean, default=True, comment="Indica si el registro está activo")
    
    # Timestamp de cuando se insertó el registro
    created_at = Column(DateTime, default=datetime.utcnow, comment="Fecha de creación")
    
    # Timestamp de la última actualización (se actualiza automáticamente)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="Fecha de actualización") 