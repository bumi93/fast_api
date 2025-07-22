# tests/test_users.py

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_and_login():
    """
    Prueba el registro de usuario, login y acceso a endpoint protegido.
    """
    # 1. Registrar un usuario
    response = client.post("/register", json={
        "name": "Test User",
        "email": "testuser@email.com",
        "password": "testpassword"
    })  # Envía una solicitud POST para registrar un nuevo usuario
    assert response.status_code == 200  # Verifica que el registro fue exitoso
    data = response.json()
    assert data["email"] == "testuser@email.com"  # Confirma que el email registrado es correcto

    # 2. Login (sin 2FA activado)
    response = client.post("/login", json={
        "email": "testuser@email.com",
        "password": "testpassword"
    })  # Realiza login con el usuario registrado
    assert response.status_code == 200  # Verifica que el login fue exitoso
    token = response.json()["access_token"]
    assert token  # Asegura que se recibió un token de acceso

    # 3. Acceder a endpoint protegido
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users", headers=headers)  # Intenta acceder a un endpoint protegido usando el token
    assert response.status_code == 200  # Verifica que el acceso fue permitido
    assert isinstance(response.json(), list)  # Confirma que la respuesta es una lista de usuarios