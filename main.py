from fastapi import FastAPI, APIRouter
from app.v1.endpoints import openai_chat, articles
from app.v1.db.events import lifespan

app = FastAPI(lifespan=lifespan)

router = APIRouter()

app.include_router(openai_chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(articles.router, prefix="/api/v1", tags=["articles"])
app.include_router(articles.router, prefix="/api/v1", tags=["articles"])
