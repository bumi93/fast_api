# app/schemas/user.py
# Esquema de validación para usuario usando Pydantic

# ¿Qué es Pydantic?
# Pydantic es una biblioteca de Python que permite la validación de datos y la creación de esquemas de datos
# utilizando anotaciones de tipo. Es ampliamente utilizada en frameworks como FastAPI para asegurar que los datos
# que recibe y envía la aplicación cumplen con las estructuras y tipos esperados. Pydantic convierte automáticamente
# los datos entrantes a los tipos especificados y lanza errores claros si los datos no son válidos.

from pydantic import BaseModel
from typing import Optional

# Esquema para la respuesta o entrada de usuario (lo que se devuelve al cliente)
class UserSchema(BaseModel):
    id: int  # Identificador único del usuario
    name: str  # Nombre del usuario
    email: str  # Correo electrónico del usuario

# Esquema para crear un usuario (lo que se recibe del cliente al crear)
# No incluye el id porque ese lo genera la base de datos automáticamente
class UserCreate(BaseModel):
    name: str  # Nombre del usuario
    email: str  # Correo electrónico del usuario
    password: str  # Contraseña del usuario

# Esquema para login de usuario
class UserLogin(BaseModel):
    email: str  # Correo electrónico del usuario
    password: str  # Contraseña del usuario
    totp_code: Optional[str] = None  # Código TOTP para 2FA (opcional en login)

# Esquema para activar 2FA
class Activate2FAResponse(BaseModel):
    qr: str  # QR en base64 para mostrar al usuario
    secret: str  # Secreto TOTP (por si se quiere mostrar también) 

# Esquema para actualizar usuario (campos opcionales)
class UserUpdate(BaseModel):
    name: Optional[str] = None  # Nombre puede ser opcional
    email: Optional[str] = None  # Email puede ser opcional
    # Puedes agregar más campos opcionales si lo deseas 