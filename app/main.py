from fastapi import FastAPI

from app.api.v1 import router as payment_v1_router
from app.core.middleware import validate_api_key


app = FastAPI()

app.add_middleware(validate_api_key)

app.include_router(payment_v1_router, prefix="/api/v1")