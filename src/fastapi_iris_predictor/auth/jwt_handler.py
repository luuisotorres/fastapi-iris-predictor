import jwt
import datetime
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi_iris_predictor.config import (
    JWT_ALGORITHM,
    JWT_EXP_DELTA_SECONDS,
    JWT_SECRET,
    settings
)

# token scheme
token_auth_scheme = HTTPBearer()


# Simple token generator for login
def create_token(username: str) -> str:
    """Generates a JWT token for a given username with an expiration timestamp.

    Args:
        username (str): The username for which the token is being generated

    Returns:
        str: A JWT token as a string
    """
    payload = {
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(
            seconds=int(JWT_EXP_DELTA_SECONDS)
        ),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def require_token(
    credentials: HTTPAuthorizationCredentials = Depends(token_auth_scheme),
):
    """
    FastAPI dependency that extracts and validates a JWT token from the
    Authorization header.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def authenticate_user(username: str, password: str) -> bool:
    """
    Validate login credentials against .env-based test user.

    Args:
        username (str): Supplied username.
        password (str): Supplied password.

    Returns:
        bool: True if credentials match, False otherwise.
    """
    return (username == settings.TEST_USERNAME
            and password == settings.TEST_PASSWORD)
