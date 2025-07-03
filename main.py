from fastapi import FastAPI, APIRouter
from app.v1.endpoints import openai_chat

app = FastAPI()

router = APIRouter()

app.include_router(openai_chat.router, prefix="/api/v1", tags=["chat"])
