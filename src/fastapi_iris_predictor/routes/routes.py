import joblib
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi_iris_predictor.database import Prediction
from fastapi_iris_predictor.auth import require_token
from fastapi_iris_predictor.database import SessionLocal
from fastapi_iris_predictor.schemas import IrisInput
from fastapi.responses import HTMLResponse


predictions_cache = {}
main_router = APIRouter()


# Load model
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT.parent / "models" / "iris_logreg_model.pkl"

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

model = joblib.load(MODEL_PATH)


# Create /predict endpoint
@main_router.post("/predict", tags=["Predictions"])
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
@main_router.get("/predictions", tags=["Predictions"])
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


# Create API root
@main_router.get("/", response_class=HTMLResponse, tags=["Root"])
async def root():
    """
    Serves the homepage with a brief description and link to Swagger UI.
    This endpoint provides a user-friendly entry point to the FastAPI
    application.
    """
    return """
        <html>
        <head>
            <title>FastAPI Iris Predictor</title>
            <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    font-family: Arial, sans-serif;
                    text-align: center;
                }
                p {
                    font-size: 1.2em;
                }
            </style>
        </head>
        <body>
            <div>
                <h1>🚀 FastAPI Iris Predictor</h1>
                <h3>Welcome to the Iris Prediction API.</h3>
                <p>👉 <a href="/docs">Access the Swagger UI here</a> to test
                the endpoints.</p>
                <p>👉 <a href="/redoc">Access the ReDoc documentation here</a>
                to explore the endpoints.</p>
            </div>
        </body>
        </html>
    """
