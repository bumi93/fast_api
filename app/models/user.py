# app/models/user.py
# Este archivo ahora importa el modelo de usuario desde app.db.models
# Se mantiene por compatibilidad con imports existentes

# Importar el modelo de usuario desde la ubicación centralizada
from app.db.models import UserDB, Base

# Re-exportar para mantener compatibilidad
__all__ = ['UserDB', 'Base'] 