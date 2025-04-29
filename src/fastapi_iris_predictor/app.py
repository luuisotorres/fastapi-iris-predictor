import datetime
import os

import joblib
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env
load_dotenv()

# Configure JWT with environment variables
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXP_DELTA_SECONDS = int(os.getenv("JWT_EXP_DELTA_SECONDS", "3600"))


# Configure SQLAlchemy
DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)


# Prediction Class
class Prediction(Base):
    """
    SQLAlchemy model for storing iris flower prediction inputs and results.

    Mapped Table:
        predictions

    Attributes:
        id (int): Primary key, auto-incremented.
        sepal_length (float): Sepal length of the iris sample.
        sepal_width (float): Sepal width of the iris sample.
        petal_length (float): Petal length of the iris sample.
        petal_width (float): Petal width of the iris sample.
        predicted_class (int): The predicted iris class label.
        created_at (datetime): Timestamp when the prediction was made.
    """
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    sepal_length = Column(Float, nullable=False)
    sepal_width = Column(Float, nullable=False)
    petal_length = Column(Float, nullable=False)
    petal_width = Column(Float, nullable=False)
    predicted_class = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# Create tables in the database
Base.metadata.create_all(engine)


# Request schema for predictions
class IrisInput(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float


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


def require_token(request: Request):
    """
    FastAPI dependency that extracts and validates a JWT token from the
    Authorization header.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401,
                            detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Load model
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "../../models/iris_logreg_model.pkl")
model = joblib.load(model_path)


# Initialize FastAPI app
app = FastAPI(
    title="FastAPI Iris Predictor",
    version="0.1.0",
    description=(
        "Simple API built with FastAPI for real-time predictions "
        "on the iris flower dataset using a Logistic Regression model."
        )
)
predictions_cache = {}


# Create /login endpoint
class LoginRequest(BaseModel):
    username: str
    password: str


TEST_USERNAME = os.getenv("TEST_USERNAME")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")
if not TEST_USERNAME or not TEST_PASSWORD:
    raise ValueError("Environment variables TEST_USERNAME and TEST_PASSWORD "
                     "must be set in .env")


@app.post("/login")
async def login(credentials: LoginRequest):
    """
    Authenticates the user and returns a JWT access token.

    Args:
        credentials (LoginRequest): Username and password payload.

    Returns:
        dict: JWT access token if authentication is successful.
    """
    if (
        credentials.username != TEST_USERNAME
        or credentials.password != TEST_PASSWORD
    ):
        raise HTTPException(status_code=401,
                            detail="Invalid username or password")
    token = create_token(credentials.username)
    return {"access_token": token}


# Create /predict endpoint
@app.post("/predict")
async def predict(input: IrisInput, user=Depends(require_token)):
    """
    Predict the iris flower class based on input features.

    Requires:
        A valid JWT token in the Authorization header.

    Args:
        input (IrisInput): Features of the iris sample.
        user (dict): Decoded JWT payload injected by the require_token
                     dependency.

    Returns:
        dict: Predicted class index.
    """
    features = (
        input.sepal_length,
        input.sepal_width,
        input.petal_length,
        input.petal_width
    )
    # Check cache
    if features in predictions_cache:
        predicted_class = predictions_cache[features]
    else:
        model_input = [list(features)]
        prediction = model.predict(model_input)
        predicted_class = int(prediction[0])
        predictions_cache[features] = predicted_class

    # Save data to database
    db = SessionLocal()
    try:
        new_prediction = Prediction(
            sepal_length=input.sepal_length,
            sepal_width=input.sepal_width,
            petal_length=input.petal_length,
            petal_width=input.petal_width,
            predicted_class=predicted_class
        )
        db.add(new_prediction)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        db.close()

    return {"predicted_class": predicted_class}


# Create /predictions endpoint
@app.get("/predictions")
async def list_predictions(limit: int = 10, offset: int = 0,
                           user=Depends(require_token)):
    """
    List stored iris predictions from the database.

    Query Parameters:
        limit (int): Number of records to return (default 10).
        offset (int): Record offset to start from (default 0).

    Requires:
        A valid JWT token in the Authorization header.

    Returns:
        List[dict]: List of prediction records.
    """
    db = SessionLocal()
    try:
        preds = (
            db.query(Prediction)
            .order_by(Prediction.id.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        results = [
            {
                "id": p.id,
                "sepal_length": p.sepal_length,
                "sepal_width": p.sepal_width,
                "petal_length": p.petal_length,
                "petal_width": p.petal_width,
                "predicted_class": p.predicted_class,
                "created_at": p.created_at.isoformat()
            }
            for p in preds
        ]
        return results
    finally:
        db.close()
