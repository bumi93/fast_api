# app/api/v1/endpoints.py
# Definición de rutas (endpoints) para la API versión 1

from fastapi import APIRouter, Depends, HTTPException, status, Response, Security
from sqlalchemy.orm import Session
from typing import List
from app.schemas.user import UserSchema, UserCreate, UserLogin, Activate2FAResponse, UserUpdate
from app.crud import user as crud_user
from app.db.session import SessionLocal
from app.utils.auth import create_access_token, decode_access_token
from app.utils.totp import generate_totp_qr
import base64
from fastapi.security import HTTPBearer

# Esquema de seguridad para JWT (HTTP Bearer)
bearer_scheme = HTTPBearer()

# Crear un router para agrupar endpoints relacionados
router = APIRouter()

# Dependencia para obtener una sesión de base de datos por cada petición
# Así cada request tiene su propia conexión y se cierra al terminar
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependencia para obtener el usuario autenticado a partir del token JWT
# Si el token es válido, devuelve el usuario; si no, lanza un error 401
# Esto se usa para proteger los endpoints que requieren autenticación
def get_current_user(token: str = Security(bearer_scheme), db: Session = Depends(get_db)):
    # El token viene como un objeto HTTPAuthorizationCredentials
    if not token or not hasattr(token, 'credentials'):
        raise HTTPException(status_code=401, detail="Token no proporcionado")
    jwt_token = token.credentials
    payload = decode_access_token(jwt_token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = crud_user.get_user_by_email(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user

# Dependencia para requerir un rol específico
from fastapi import Depends, HTTPException

def require_role(required_role: str):
    def role_checker(current_user=Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="No tienes permisos suficientes")
        return current_user
    return role_checker

# Endpoint raíz que responde con un mensaje de bienvenida
@router.get("/")
def read_root():
    return {"message": "¡Hola desde FastAPI!"}

# --- Autenticación y 2FA ---

# Endpoint para registrar un nuevo usuario
@router.post("/register", response_model=UserSchema)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        if crud_user.get_user_by_email(db, user.email):
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        return crud_user.register_user(db, user)
    except Exception as e:
        print("ERROR EN REGISTRO:", e)
        raise

# Endpoint para activar 2FA y devolver el QR en base64
@router.post("/users/{user_id}/2fa/activate", response_model=Activate2FAResponse)
def activate_2fa(user_id: int, db: Session = Depends(get_db)):
    secret = crud_user.activate_2fa(db, user_id)
    if not secret:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    qr_bytes = generate_totp_qr(str(user_id), secret)
    qr_b64 = base64.b64encode(qr_bytes).decode()
    return Activate2FAResponse(qr=qr_b64, secret=secret)

# Endpoint de login
@router.post("/login")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = crud_user.login_user(db, login_data)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales o código 2FA incorrectos")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# --- CRUD de usuarios (protegido) ---

# Endpoint protegido: obtener todos los usuarios (requiere autenticación JWT)
@router.get("/users", response_model=List[UserSchema])
def read_users(
    skip: int = 0,  # Número de usuarios a saltar (para paginación)
    limit: int = 10,  # Número máximo de usuarios a devolver (para paginación)
    name: str = None,  # Filtro opcional por nombre
    email: str = None,  # Filtro opcional por email
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Devuelve la lista de usuarios con paginación y filtros opcionales por nombre y email (requiere autenticación).
    - skip: cuántos usuarios saltar (por defecto 0)
    - limit: cuántos usuarios devolver (por defecto 10)
    - name: filtra usuarios por nombre (opcional)
    - email: filtra usuarios por email (opcional)
    """
    query = db.query(crud_user.UserDB)
    if name:
        query = query.filter(crud_user.UserDB.name.ilike(f"%{name}%"))
    if email:
        query = query.filter(crud_user.UserDB.email.ilike(f"%{email}%"))
    users = query.offset(skip).limit(limit).all()
    return users

# Endpoint protegido: obtener un usuario por su ID (requiere autenticación JWT)
@router.get("/users/{user_id}", response_model=UserSchema)
def read_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Devuelve un usuario específico por su ID (requiere autenticación)."""
    db_user = crud_user.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user

# Endpoint protegido: actualizar un usuario existente (requiere autenticación JWT)
@router.put("/users/{user_id}", response_model=UserSchema)
def update_user(
    user_id: int,
    user: UserUpdate,  # Ahora acepta el nuevo esquema con campos opcionales
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Actualiza los datos de un usuario existente (requiere autenticación).
    Ahora puedes enviar solo el campo que quieras actualizar.
    Solo un admin puede cambiar el rol de un usuario.
    """
    db_user = crud_user.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    # Solo actualiza los campos que se envían
    if user.name is not None:
        db_user.name = user.name
    if user.email is not None:
        db_user.email = user.email
    if user.role is not None:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Solo un admin puede cambiar el rol de un usuario")
        db_user.role = user.role
    db.commit()
    db.refresh(db_user)
    return db_user

# Endpoint protegido: borrar un usuario (requiere autenticación JWT y rol admin)
@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))  # Solo admin puede borrar usuarios
):
    """
    Elimina un usuario de la base de datos (requiere autenticación y rol admin).
    """
    success = crud_user.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"ok": True, "message": "Usuario eliminado"} 