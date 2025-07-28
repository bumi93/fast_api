# app/db/session.py
# Configuración de la base de datos usando SQLAlchemy
# Este archivo se encarga de conectar la aplicación con la base de datos y preparar todo para poder guardar y leer datos.

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
import os

# Usamos SQLite para este ejemplo
# DATABASE_URL es la dirección donde se guardará la base de datos.
# Ahora la base de datos se guardará en la carpeta 'data' dentro del proyecto.
db_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
os.makedirs(db_folder, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(db_folder, 'test.db')}"

# Creamos el 'engine', que es el motor que se conecta y habla con la base de datos.
# 'check_same_thread': False es necesario para que SQLite funcione bien con FastAPI.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal es una fábrica de sesiones. Cada vez que queremos guardar o leer algo,
# creamos una "sesión" usando esto. Así podemos trabajar con la base de datos de forma segura.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# metadata guarda información sobre las tablas y estructuras de la base de datos.
metadata = MetaData()

# Función para obtener una sesión de base de datos
def get_db():
    """
    Dependencia para obtener una sesión de base de datos por cada petición.
    Así cada request tiene su propia conexión y se cierra al terminar.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 