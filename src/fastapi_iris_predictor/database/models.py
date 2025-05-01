import datetime
from sqlalchemy import Column, Integer, Float, DateTime
from .base import Base


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
