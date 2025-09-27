import os
from mangum import Mangum
from src.app.main import app

api_base_path = os.getenv("API_BASE_PATH") or ""
handler = Mangum(app, api_gateway_base_path=api_base_path)
