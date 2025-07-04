from fastapi import FastAPI, APIRouter
from app.v1.endpoints import openai_chat, download_articles
from app.v1.db.events import init_db

app = FastAPI()

init_db(app)

router = APIRouter()

app.include_router(openai_chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(
    download_articles.router, prefix="/api/v1", tags=["search_download_articles"]
)
