# app/api/v1/endpoints.py
# Definición de rutas (endpoints) para la API versión 1

from fastapi import APIRouter, Depends, HTTPException, status, Response, Security, Request
from sqlalchemy.orm import Session
from typing import List
from app.schemas.user import UserSchema, UserCreate, UserLogin, Activate2FAResponse, UserUpdate
from app.crud import user as crud_user
from app.db.session import SessionLocal
from app.utils.auth import create_access_token, decode_access_token
from app.utils.totp import generate_totp_qr
import base64
from fastapi.security import HTTPBearer
from app.schemas.scraping import AribaLoginRequest
from app.scraping.ariba_scraper import login_ariba, AribaCredentials, descarga_db
from app.data_management import FileProcessor, DataValidator, DataTransformer
from app.api.v1.upload_endpoints import router as upload_router
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncio
import logging
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurar templates
templates = Jinja2Templates(directory="app/templates")

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

# Incluir el router de upload
router.include_router(upload_router)

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


# Variable global para la tarea de refresco
refresh_task = None

# Diccionario global para drivers activos y variable de uso
active_drivers = {}
driver_in_use = False

# Este bloque crea un "ThreadPoolExecutor", que es una herramienta de Python para ejecutar tareas en paralelo usando hilos (threads).
# En este caso, se usa para ejecutar tareas relacionadas con Selenium (como automatizar el navegador) sin bloquear el hilo principal de la aplicación.
# El parámetro "max_workers=2" significa que como máximo se ejecutarán 2 tareas al mismo tiempo en segundo plano.
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=1)

logger = logging.getLogger(__name__)

def set_driver_in_use(in_use: bool):
    """Establece el estado de uso del driver"""
    global driver_in_use
    driver_in_use = in_use
    logger.info(f"Driver usage state set to: {in_use}")

async def refresh_driver_periodically(driver_name: str, interval: int):
    """
    Tarea asíncrona para navegar a URLs específicas periódicamente
    Solo se ejecuta si el driver no está siendo usado activamente
    """
    global driver_in_use
    logger.info(f"Iniciando tarea de navegación para {driver_name} con intervalo de {interval} segundos")
    while True:
        try:
            logger.info(f"Esperando {interval} segundos antes de la próxima navegación para {driver_name}")
            await asyncio.sleep(interval)
            # Verificar si el driver está activo
            if driver_name not in active_drivers:
                logger.warning(f"No hay driver activo para {driver_name}, saltando navegación")
                continue
            # Verificar si el driver está siendo usado
            if driver_in_use:
                logger.info(f"Driver {driver_name} está siendo usado, saltando navegación")
                continue
            logger.info(f"Iniciando navegación para {driver_name}")
            driver = active_drivers[driver_name]
            # Navegar a la primera URL
            logger.info(f"Navegando a primera URL para {driver_name}")
            driver.get('https://s1.ariba.com/Sourcing/Main')
            await asyncio.sleep(2)
            # Navegar a la segunda URL
            logger.info(f"Navegando a segunda URL para {driver_name}")
            driver.get('https://s1.ariba.com/Sourcing/Main/aw?awh=r&awssk=XT7J.wXPZ1._CF9T&realm=latam&awrdt=1')
            await asyncio.sleep(2)
            logger.info(f"Navegación completada exitosamente para {driver_name}")
        except Exception as e:
            logger.error(f"Error en la tarea de navegación para {driver_name}: {str(e)}")
            logger.info("Esperando 60 segundos antes de reintentar...")
            await asyncio.sleep(60)

# Endpoint para login con Selenium y refresco automático
@router.post("/login-ariba-driver")
async def login_ariba_driver():
    """
    Inicia sesión en Ariba usando las credenciales del driver principal y lanza la tarea de refresco.
    """
    global refresh_task
    logger.info("[login-ariba-driver] Iniciando endpoint")
    creds = AribaCredentials.get_credentials("driver")
    if not creds:
        logger.error("[login-ariba-driver] Credenciales no encontradas para 'driver'")
        raise HTTPException(status_code=404, detail="Credenciales no encontradas para 'driver'")
    driver, success, message = login_ariba(
        email=creds["email"],
        password=creds["password"],
        headless=False
    )
    logger.info(f"[login-ariba-driver] Resultado login: success={success}, message={message}")
    if success:
        active_drivers["driver"] = driver  # Guarda el driver activo
        logger.info("[login-ariba-driver] Driver guardado en active_drivers['driver']")
        # Lanza la tarea de refresco solo si no existe o está terminada
        if refresh_task is None or refresh_task.done():
            logger.info("[login-ariba-driver] Lanzando tarea de refresco para 'driver'")
            refresh_task = asyncio.create_task(refresh_driver_periodically("driver", 90))
        else:
            logger.info("[login-ariba-driver] Tarea de refresco ya activa")
        return {"status": "success", "message": message}
    else:
        logger.error(f"[login-ariba-driver] Error en login: {message}")
        raise HTTPException(status_code=500, detail=message)

@router.post("/login-ariba-driver_m")
async def login_ariba_driver_m():
    """
    Inicia sesión en Ariba usando las credenciales del driver_m y lanza la tarea de refresco.
    """
    global refresh_task
    creds = AribaCredentials.get_credentials("driver_m")
    if not creds:
        raise HTTPException(status_code=404, detail="Credenciales no encontradas para 'driver_m'")
    driver, success, message = login_ariba(
        email=creds["email"],
        password=creds["password"],
        headless=False
    )
    if success:
        active_drivers["driver_m"] = driver  # Guarda el driver activo
        if refresh_task is None or refresh_task.done():
            refresh_task = asyncio.create_task(refresh_driver_periodically("driver_m", 90))
        return {"status": "success", "message": message}
    else:
        raise HTTPException(status_code=500, detail=message)

# Endpoint para cerrar el driver y cancelar la tarea de refresco
@router.post("/close-driver/{driver_name}")
async def close_driver(driver_name: str):
    """
    Cierra el driver especificado y cancela la tarea de refresco si está activa.
    """
    global refresh_task
    if driver_name in active_drivers:
        try:
            active_drivers[driver_name].quit()
            del active_drivers[driver_name]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al cerrar el driver: {str(e)}")
    # Cancela la tarea de refresco si está activa
    if refresh_task and not refresh_task.done():
        refresh_task.cancel()
        try:
            await refresh_task
        except asyncio.CancelledError:
            pass
        refresh_task = None
    return {"status": "success", "message": f"Driver {driver_name} cerrado y refresco detenido"}

# Endpoint para descargar archivos CSV desde Ariba
# Este endpoint de FastAPI permite descargar archivos CSV desde Ariba usando un driver de Selenium que ya debe estar autenticado y activo.
@router.post("/descargar-archivos-ariba")
async def descargar_archivos_ariba(path: str = None):
    """
    Descarga archivos CSV desde Ariba usando el driver principal (driver)
    
    Args:
        path: Ruta opcional donde guardar los archivos (por defecto usa DOWNLOAD_DIR)
        
    Returns:
        dict: Estado de la descarga y mensaje
    """
    try:
        driver_name = "driver"  # Siempre se usa el driver principal llamado "driver"
        
        # 1. Verifica que el driver esté activo. Si no, lanza un error.
        if driver_name not in active_drivers:
            raise HTTPException(
                status_code=400,
                detail=f"No hay un driver activo. Primero debes iniciar sesión con /login-ariba-driver"
            )
        
        driver = active_drivers[driver_name]
        logger.info(f"Iniciando descarga de archivos con driver {driver_name}")
        
        # 2. Si no se especifica una ruta, usa la ruta por defecto de configuración.
        if path is None:
            from app.core.config import DOWNLOAD_DIR
            path = DOWNLOAD_DIR
        
        # 3. Marca el driver como "en uso" para evitar conflictos con otras operaciones.
        set_driver_in_use(True)
        logger.info(f"Driver {driver_name} marcado como en uso - iniciando descarga")
        
        try:
            # 4. Ejecuta la función de descarga (descarga_db) de forma asíncrona en un thread pool.
            #    Esto permite que la API no se bloquee mientras Selenium descarga los archivos.
            loop = asyncio.get_event_loop()
            success, message = await loop.run_in_executor(
                executor,
                lambda: descarga_db(driver, path)
            )
            
            # 5. Si la descarga fue exitosa, retorna un diccionario con el estado y detalles.
            if success:
                return {
                    "status": "success",
                    "message": message,
                    "driver_used": driver_name,
                    "download_path": path
                }
            else:
                # Si hubo un error en la descarga, lanza un error HTTP 500.
                raise HTTPException(status_code=500, detail=message)
                
        finally:
            # 6. Al terminar (éxito o error), marca el driver como "libre".
            set_driver_in_use(False)
            logger.info(f"Driver {driver_name} marcado como libre - descarga completada")
            
    except HTTPException:
        # Si ya se lanzó un HTTPException, simplemente la relanza.
        raise
    except Exception as e:
        # Si ocurre cualquier otro error, lo registra y lanza un error HTTP 500.
        logger.error(f"Error en descarga de archivos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en descarga de archivos: {str(e)}")

# --- Endpoints de Manejo de Datos ---
# Estos endpoints permiten procesar, validar y transformar archivos CSV descargados de Ariba

@router.get("/data/files")
async def get_available_files():
    """
    Obtiene la lista de archivos CSV disponibles en la carpeta de descargas
    
    Este endpoint:
    1. Busca todos los archivos CSV en la carpeta de descargas
    2. Retorna una lista con los nombres de archivos encontrados
    3. Incluye el conteo total de archivos
    
    Returns:
        dict: Diccionario con status, files_count y lista de archivos
        
    Ejemplo de respuesta:
        {
            "status": "success",
            "files_count": 3,
            "files": ["archivo1.csv", "archivo2.csv", "archivo3.csv"]
        }
    """
    try:
        from app.core.config import DOWNLOAD_DIR
        file_processor = FileProcessor(DOWNLOAD_DIR)
        files = file_processor.get_available_files()
        
        return {
            "status": "success",
            "files_count": len(files),
            "files": files
        }
    except Exception as e:
        logger.error(f"Error al obtener archivos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener archivos: {str(e)}")

@router.get("/data/files/{filename}/info")
async def get_file_info(filename: str):
    """
    Obtiene información detallada de un archivo específico
    
    Este endpoint:
    1. Carga el archivo CSV especificado
    2. Analiza su estructura (filas, columnas, tipos de datos)
    3. Obtiene metadatos (tamaño, fecha de modificación)
    4. Retorna información detallada del archivo
    
    Args:
        filename: Nombre del archivo CSV (ejemplo: "Backlog COMPRAS - LATAM - PR's.csv")
    
    Returns:
        dict: Diccionario con status y información detallada del archivo
        
    Ejemplo de respuesta:
        {
            "status": "success",
            "file_info": {
                "filename": "archivo.csv",
                "file_size_mb": 2.5,
                "rows": 1000,
                "columns": 15,
                "column_names": ["col1", "col2", ...]
            }
        }
    """
    try:
        from app.core.config import DOWNLOAD_DIR
        file_processor = FileProcessor(DOWNLOAD_DIR)
        file_info = file_processor.get_file_info(filename)
        
        return {
            "status": "success",
            "file_info": file_info
        }
    except Exception as e:
        logger.error(f"Error al obtener información del archivo {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener información del archivo: {str(e)}")

@router.post("/data/validate")
async def validate_files(filenames: List[str] = None):
    """
    Valida múltiples archivos CSV
    
    Este endpoint:
    1. Carga los archivos CSV especificados (o todos si no se especifican)
    2. Aplica validaciones de calidad de datos
    3. Verifica estructura y completitud
    4. Genera un reporte de validación con estadísticas
    
    Args:
        filenames: Lista opcional de nombres de archivos a validar
                  Si no se especifica, valida todos los archivos disponibles
    
    Returns:
        dict: Diccionario con status, resumen de validación y resultados detallados
        
    Ejemplo de respuesta:
        {
            "status": "success",
            "validation_summary": {
                "total_files": 3,
                "files_with_errors": 0,
                "files_with_warnings": 1,
                "average_completeness": 95.5
            },
            "validation_results": {...}
        }
    """
    try:
        from app.core.config import DOWNLOAD_DIR
        file_processor = FileProcessor(DOWNLOAD_DIR)
        validator = DataValidator()
        
        if filenames is None:
            filenames = file_processor.get_available_files()
        
        validation_results = validator.validate_multiple_files(file_processor, filenames)
        summary = validator.get_validation_summary(validation_results)
        
        return {
            "status": "success",
            "validation_summary": summary,
            "validation_results": validation_results
        }
    except Exception as e:
        logger.error(f"Error en validación de archivos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en validación: {str(e)}")

@router.post("/data/transform")
async def transform_files(filenames: List[str] = None, save_clean: bool = False):
    """
    Transforma y limpia múltiples archivos CSV
    
    Este endpoint:
    1. Carga los archivos CSV especificados (o todos si no se especifican)
    2. Aplica limpiezas y transformaciones estándar
    3. Elimina duplicados y maneja valores faltantes
    4. Normaliza nombres de columnas y formatos
    5. Opcionalmente guarda los archivos limpios
    
    Args:
        filenames: Lista opcional de nombres de archivos a transformar
                  Si no se especifica, transforma todos los archivos disponibles
        save_clean: Si es True, guarda los archivos limpios en una carpeta "clean_data"
    
    Returns:
        dict: Diccionario con status, resumen de transformación y archivos guardados
        
    Ejemplo de respuesta:
        {
            "status": "success",
            "transformation_summary": {
                "total_transformations": 5,
                "transformations_applied": ["Removed duplicates", "Cleaned column names", ...]
            },
            "files_transformed": 3,
            "saved_files": {...}
        }
    """
    try:
        from app.core.config import DOWNLOAD_DIR
        file_processor = FileProcessor(DOWNLOAD_DIR)
        transformer = DataTransformer()
        
        if filenames is None:
            filenames = file_processor.get_available_files()
        
        transformed_data = transformer.transform_multiple_files(file_processor, filenames)
        transformation_summary = transformer.get_transformation_summary()
        
        result = {
            "status": "success",
            "transformation_summary": transformation_summary,
            "files_transformed": len(transformed_data)
        }
        
        if save_clean:
            # Crear carpeta para archivos limpios
            clean_folder = os.path.join(DOWNLOAD_DIR, "clean_data")
            os.makedirs(clean_folder, exist_ok=True)
            
            saved_files = transformer.save_transformed_data(transformed_data, clean_folder)
            result["saved_files"] = saved_files
            result["clean_folder"] = clean_folder
        
        return result
    except Exception as e:
        logger.error(f"Error en transformación de archivos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en transformación: {str(e)}")

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