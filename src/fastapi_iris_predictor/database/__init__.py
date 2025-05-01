from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi_iris_predictor.config import DB_URL
from .models import Prediction

from .base import Base


# Configure SQLAlchemy
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


Base.metadata.create_all(engine)

__all__ = ['Prediction']
