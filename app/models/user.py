# app/models/user.py
# Este archivo define cómo es un usuario en la base de datos y cómo se valida la información de un usuario en la API.
# Usamos dos tipos de modelos: uno para la base de datos (SQLAlchemy) y otro para la validación de datos (Pydantic).

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

# Creamos una clase base para los modelos de la base de datos usando SQLAlchemy.
# Esto permite que todos los modelos compartan la misma configuración.
Base = declarative_base()

# Modelo de usuario para la base de datos (SQLAlchemy)
# Esta clase define cómo se guarda un usuario en la base de datos.
# Cada atributo es una columna en la tabla 'users'.
class UserDB(Base):
    __tablename__ = "users"  # Nombre de la tabla en la base de datos
    id = Column(Integer, primary_key=True, index=True)  # ID único para cada usuario
    name = Column(String, index=True)  # Nombre del usuario
    email = Column(String, unique=True, index=True)  # Correo electrónico, debe ser único
    password = Column(String)  # Contraseña hasheada del usuario
    totp_secret = Column(String, nullable=True)  # Secreto TOTP para 2FA (puede ser nulo si no está activado)
    role = Column(String, default="user")  # Rol del usuario (user, admin, etc.)

# Modelo de usuario para validación y respuesta (Pydantic)
# Esta clase se usa para validar los datos que entran y salen de la API.
# No está conectada directamente a la base de datos, solo sirve para asegurarse de que los datos sean correctos.
class User(BaseModel):
    id: int  # Identificador único del usuario
    name: str  # Nombre del usuario
    email: str  # Correo electrónico del usuario 