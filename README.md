# Bots-Latam v2

Proyecto base con FastAPI, autenticación JWT y 2FA (Microsoft Authenticator)

## Descripción

Esta API está construida con FastAPI y permite gestionar usuarios con autenticación segura (JWT) y verificación en dos pasos (2FA) usando Microsoft Authenticator o cualquier app compatible con TOTP.

## Estructura principal
- CRUD de usuarios (crear, leer, actualizar, borrar)
- Registro y login seguro
- Activación de 2FA con QR
- Endpoints protegidos con token JWT

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/bumi93/fast_api.git
   cd fast_api
   ```
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Crea la base de datos:
   ```bash
   python create_db.py
   ```
4. Inicia el servidor:
   ```bash
   uvicorn app.main:app --reload
   ```

## Uso básico

1. Ve a [http://localhost:8000/docs](http://localhost:8000/docs) para usar la documentación interactiva (Swagger UI).
2. Registra un usuario con `/register`.
3. Activa 2FA con `/users/{user_id}/2fa/activate` y escanea el QR con Microsoft Authenticator.
4. Haz login con `/login` usando email, contraseña y el código de la app. Copia el `access_token`.
5. Haz clic en "Authorize" (candado) y pega tu token así:
   ```
   Bearer TU_TOKEN
   ```
6. Accede a los endpoints protegidos (`/users`, `/users/{user_id}`, etc.).

## Variables de entorno
Crea un archivo `.env` para tus claves secretas y configuraciones sensibles (recomendado para producción).

## Pruebas
Puedes agregar y ejecutar pruebas en la carpeta `tests/` usando `pytest`.

## Seguridad
- No subas tu archivo `.env` ni bases de datos locales al repositorio.
- Cambia la clave secreta por una variable de entorno en producción.

---

¿Dudas o sugerencias? ¡Contribuciones y feedback son bienvenidos! 