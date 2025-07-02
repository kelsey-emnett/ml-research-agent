from fastapi import FastAPI, APIRouter
from app.v1.endpoints import openai_chat, download_articles

app = FastAPI()

router = APIRouter()

app.include_router(openai_chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(
    download_articles.router, prefix="/api/v1", tags=["search_download_articles"]
)
