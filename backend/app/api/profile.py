from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import require_valid_api_key
from app.db.database import get_session
from app.tools.tracker import ProfileStore

router = APIRouter(prefix="/api/profile", tags=["profile"], dependencies=[Depends(require_valid_api_key)])


class ProfileValue(BaseModel):
    key: str
    value: str


@router.get("")
async def get_profile(session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    profile = ProfileStore(session)
    return await profile.all_values()


@router.post("")
async def set_profile_value(request: ProfileValue, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    profile = ProfileStore(session)
    await profile.set_value(key=request.key, value=request.value)
    return {"saved": request.key}


@router.delete("/{key}")
async def delete_profile_value(key: str, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    from sqlmodel import select

    from app.db.models import ProfileEntry

    statement = select(ProfileEntry).where(ProfileEntry.key == key)
    entry = (await session.execute(statement)).scalars().first()
    if entry is not None:
        await session.delete(entry)
        await session.commit()
    return {"deleted": key}