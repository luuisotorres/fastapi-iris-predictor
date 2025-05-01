from fastapi import FastAPI
from .routes import main_router, auth_router

# Initialize FastAPI app 
app = FastAPI(
    title="FastAPI Iris Predictor",
    version="0.1.0",
    description=(
        "Simple API built with FastAPI for real-time predictions "
        "on the iris flower dataset using a Logistic Regression model."
        )
)


app.include_router(auth_router)
app.include_router(main_router)
