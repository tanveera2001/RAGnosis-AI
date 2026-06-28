import os

from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME")
API_HOST = os.getenv("API_HOST")
API_PORT = int(os.getenv("API_PORT", 8000))
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))
