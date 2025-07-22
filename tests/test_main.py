# tests/test_main.py
# Pruebas para el endpoint raíz de la aplicación FastAPI

from fastapi.testclient import TestClient
from app.main import app

# Crear un cliente de pruebas para la aplicación
client = TestClient(app)

# Probar que el endpoint raíz responde correctamente
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "¡Hola desde FastAPI!"} 