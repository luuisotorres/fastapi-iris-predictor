from pydantic import BaseModel


class IrisInput(BaseModel):
    """
    Pydantic model for Iris flower features input.


    Args:
        BaseModel (pydantic.BaseModel): Base for feating data
        models with validation.
    """
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float
