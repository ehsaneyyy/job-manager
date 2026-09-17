from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import settings

async_engine = create_async_engine(settings.database_url, echo=False, future=True)

async_session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_factory() as session:
        yield session


async def initialize_database() -> None:
    import app.db.models  # noqa: F401

    async with async_engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)
    settings.ensure_directories()