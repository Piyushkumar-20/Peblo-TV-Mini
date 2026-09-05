import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
bearer_scheme = HTTPBearer()

from app.core.config import settings
from app.db.session import get_db
from app.models import User, UserRole


PASSWORD_ITERATIONS = 310_000
TOKEN_EXPIRE_SECONDS = 8 * 60 * 60

bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)

    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )

    return (
        f"pbkdf2_sha256${PASSWORD_ITERATIONS}$"
        f"{base64.urlsafe_b64encode(salt).decode()}$"
        f"{base64.urlsafe_b64encode(derived_key).decode()}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_text, expected_text = (
            password_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(expected_text.encode())

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )

        return hmac.compare_digest(actual, expected)

    except (ValueError, TypeError):
        return False


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def create_access_token(user: User) -> str:
    now = int(time.time())

    header = {
        "alg": "HS256",
        "typ": "JWT",
    }

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value,
        "iat": now,
        "exp": now + TOKEN_EXPIRE_SECONDS,
    }

    encoded_header = _base64url(
        json.dumps(
            header,
            separators=(",", ":"),
        ).encode()
    )

    encoded_payload = _base64url(
        json.dumps(
            payload,
            separators=(",", ":"),
        ).encode()
    )

    message = f"{encoded_header}.{encoded_payload}".encode()

    signature = hmac.new(
        settings.auth_secret.encode("utf-8"),
        message,
        hashlib.sha256,
    ).digest()

    return f"{encoded_header}.{encoded_payload}.{_base64url(signature)}"


def decode_access_token(token: str) -> dict:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")

        message = f"{encoded_header}.{encoded_payload}".encode()

        expected_signature = hmac.new(
            settings.auth_secret.encode("utf-8"),
            message,
            hashlib.sha256,
        ).digest()

        provided_signature = _base64url_decode(encoded_signature)

        if not hmac.compare_digest(
            expected_signature,
            provided_signature,
        ):
            raise ValueError("Invalid signature")

        payload = json.loads(
            _base64url_decode(encoded_payload).decode()
        )

        if int(payload["exp"]) < int(time.time()):
            raise ValueError("Token expired")

        return payload

    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    payload = decode_access_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    user = db.get(User, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user


def require_editor(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in {
        UserRole.EDITOR,
        UserRole.ADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Editor access required.",
        )

    return current_user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    return current_user


def bootstrap_user(
    db: Session,
    email: str,
    password: str,
    role: UserRole,
) -> User:
    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if user is None:
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user