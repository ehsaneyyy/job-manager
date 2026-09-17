import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.agent import agent_respond
from app.core.api import APIModel
from app.core.security import require_valid_api_key
from app.db.database import get_session
from app.tools.tracker import ConversationLog

router = APIRouter(prefix="/api/chat", tags=["chat"], dependencies=[Depends(require_valid_api_key)])

logger = logging.getLogger("jobmanager.chat")


class SendRequest(APIModel):
    message: str


class SendResponse(APIModel):
    reply: str
    tools_used: list[str]
    user_message: str


class HistoryResponse(APIModel):
    messages: list[dict]


@router.post("/send", response_model=SendResponse)
async def send_message(request: SendRequest, session: AsyncSession = Depends(get_session)) -> SendResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    conversation = ConversationLog(session)
    await conversation.append(role="user", content=request.message)

    recent_history = await conversation.history(limit=30)
    message_history = [
        {"role": message.role, "content": message.content}
        for message in recent_history
        if message.content
    ]

    try:
        agent_result = await agent_respond(
            user_message=request.message,
            message_history=message_history,
            session=session,
        )
    except Exception as exc:
        logger.error("Agent failed: %s\n%s", exc, traceback.format_exc())
        error_reply = (
            "I could not reach the AI provider. Check that LLM_API_KEY and LLM_MODEL are configured "
            f"in backend\\.env and that your internet is on. (Details: {exc})"
        )
        await conversation.append(role="assistant", content=error_reply, tool_used="error")
        return SendResponse(reply=error_reply, tools_used=[], user_message=request.message)

    await conversation.append(role="assistant", content=agent_result["reply"], tool_used=", ".join(agent_result["tools_used"]))
    return SendResponse(
        reply=agent_result["reply"],
        tools_used=agent_result["tools_used"],
        user_message=request.message,
    )


@router.get("/history", response_model=HistoryResponse)
async def chat_history(session: AsyncSession = Depends(get_session)) -> HistoryResponse:
    conversation = ConversationLog(session)
    messages = await conversation.history(limit=100)
    return HistoryResponse(
        messages=[
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "toolUsed": message.tool_used,
                "createdAt": message.created_at.isoformat() if message.created_at else None,
            }
            for message in messages
        ]
    )