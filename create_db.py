# create_db.py
# Script para crear las tablas de la base de datos

# Importa el engine de la base de datos (la conexión)
from app.db.session import engine
# Importa la clase Base, que contiene los modelos de las tablas
from app.db.models import Base

# Crea todas las tablas definidas en los modelos que heredan de Base
Base.metadata.create_all(bind=engine)

# Mensaje para indicar que las tablas se crearon correctamente
print("¡Tablas creadas exitosamente!") 