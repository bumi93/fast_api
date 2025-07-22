# app/crud/user.py
# Funciones CRUD para el modelo de usuario usando SQLAlchemy

from sqlalchemy.orm import Session
from app.models.user import UserDB
from app.schemas.user import UserCreate, UserLogin
from typing import List, Optional
from app.utils.auth import get_password_hash, verify_password
from app.utils.totp import generate_totp_secret, verify_totp_code

# Obtener todos los usuarios de la base de datos
def get_users(db: Session) -> List[UserDB]:
    return db.query(UserDB).all()  # Devuelve una lista con todos los usuarios de la tabla 'users'

def get_user(db: Session, user_id: int) -> Optional[UserDB]:
    return db.query(UserDB).filter(UserDB.id == user_id).first()  # Busca y retorna el usuario con el id dado (o None si no existe)

def get_user_by_email(db: Session, email: str) -> Optional[UserDB]:
    return db.query(UserDB).filter(UserDB.email == email).first()  # Busca y retorna el usuario con el email dado (o None si no existe)

def register_user(db: Session, user: UserCreate) -> UserDB:
    hashed_password = get_password_hash(user.password)  # Hashea la contraseña del usuario
    db_user = UserDB(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role="user"  # Siempre asigna 'user' al registrar
    )
    db.add(db_user)  # Agrega el usuario a la sesión de la base de datos
    db.commit()  # Guarda los cambios en la base de datos
    db.refresh(db_user)  # Refresca la instancia para obtener el id generado
    return db_user  # Retorna el usuario creado

def activate_2fa(db: Session, user_id: int) -> str:
    db_user = get_user(db, user_id)  # Busca el usuario por id
    if db_user is None:
        return None  # Si no existe, retorna None
    secret = generate_totp_secret()  # Genera un secreto TOTP para 2FA
    db_user.totp_secret = secret  # Asigna el secreto al usuario
    db.commit()  # Guarda los cambios en la base de datos
    db.refresh(db_user)  # Refresca la instancia del usuario
    return secret  # Retorna el secreto generado

def login_user(db: Session, login_data: UserLogin) -> Optional[UserDB]:
    db_user = get_user_by_email(db, login_data.email)  # Busca el usuario por email
    if db_user is None:
        return None  # Si no existe, retorna None
    if not verify_password(login_data.password, db_user.password):
        return None  # Si la contraseña no coincide, retorna None
    if db_user.totp_secret:  # Si el usuario tiene 2FA activado
        if not login_data.totp_code or not verify_totp_code(db_user.totp_secret, login_data.totp_code):
            return None  # Si el código TOTP no es válido, retorna None
    return db_user  # Si todo es correcto, retorna el usuario

def delete_user(db: Session, user_id: int) -> bool:
    """
    Elimina un usuario de la base de datos por su ID.
    Retorna True si se eliminó, False si no existe.
    """
    db_user = get_user(db, user_id)
    if db_user is None:
        return False  # No existe el usuario
    db.delete(db_user)
    db.commit()
    return True