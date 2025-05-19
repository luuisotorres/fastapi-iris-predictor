import os
from dotenv import load_dotenv
# Load environment variables from .env
load_dotenv()
# Configure JWT with environment variables
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXP_DELTA_SECONDS = int(os.getenv("JWT_EXP_DELTA_SECONDS", "3600"))
# Database
DB_URL = os.getenv("DATABASE_URL")
# Username and password
TEST_USERNAME = os.getenv("TEST_USERNAME")
TEST_PASSWORD = os.getenv("TEST_PASSWORD")
if not TEST_USERNAME or not TEST_PASSWORD:
    raise ValueError("Environment variables TEST_USERNAME and TEST_PASSWORD "
                     "must be set in .env")
