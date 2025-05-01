from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from fastapi_iris_predictor.auth import (
    create_token,
    authenticate_user
)

auth_router = APIRouter(tags=["Authentication"])


# Create /login endpoint
class LoginRequest(BaseModel):
    username: str
    password: str


@auth_router.post("/login")
async def login(credentials: LoginRequest):
    """
    Authenticates the user and returns a JWT access token.

    Args:
        credentials (LoginRequest): Username and password payload.

    Returns:
        dict: JWT access token if authentication is successful.
    """
    if not authenticate_user(credentials.username, credentials.password):
        HTTPException(status_code=401,
                      detail="Invalid username or password")
    token = create_token(credentials.username)
    return {"access_token": token}
