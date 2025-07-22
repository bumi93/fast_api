# app/utils/totp.py
# Utilidades para 2FA (autenticación en dos pasos) usando TOTP compatible con Microsoft Authenticator

import pyotp
import qrcode
import io

# Genera un secreto TOTP para un usuario (debe guardarse en la base de datos)
def generate_totp_secret() -> str:
    return pyotp.random_base32()

# Genera un código QR para configurar la app de autenticación (Microsoft Authenticator, Google Authenticator, etc.)
def generate_totp_qr(username: str, secret: str, issuer: str = "BotsLatam") -> bytes:
    # Formato estándar para apps de autenticación
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)
    qr = qrcode.make(uri)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    return buf.getvalue()

# Verifica si el código TOTP ingresado es válido para el secreto guardado
def verify_totp_code(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code) 