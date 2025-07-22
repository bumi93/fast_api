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
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@email.com"

    # 2. Login (sin 2FA activado)
    response = client.post("/login", json={
        "email": "testuser@email.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token

    # 3. Acceder a endpoint protegido
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list) 