import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, emails, jobs, profile, stats
from app.core.config import settings
from app.core.scheduler import scheduler_loop
from app.db.database import initialize_database

logger = logging.getLogger("jobmanager.main")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(title="Job Manager", version="1.0.0")


@app.on_event("startup")
async def on_startup() -> None:
    await initialize_database()
    app.state.scheduler_task = asyncio.create_task(scheduler_loop())
    logger.info("Database ready at %s", settings.data_dir)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    task = getattr(app.state, "scheduler_task", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(jobs.router)
app.include_router(emails.router)
app.include_router(stats.router)
app.include_router(profile.router)
app.include_router(auth.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "llm_provider": settings.llm_provider}