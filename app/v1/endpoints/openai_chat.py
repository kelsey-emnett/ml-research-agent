from fastapi import APIRouter, HTTPException
from app.v1.client.openai_chat import OpenAIChat
from app.v1.schemas.openai_chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat/", tags=["chat"], response_model=ChatResponse)
async def post_chat(request: ChatRequest):
    try:
        chat_cls = OpenAIChat()
        chat_response = chat_cls.chat(request.system_message, request.user_message)

        return {"response": chat_response}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing chat request: {str(e)}"
        )
