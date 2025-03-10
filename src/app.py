import platform
import uvicorn
from contextlib import asynccontextmanager
from a2wsgi import ASGIMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import logger, settings, session_manager
import sentry_sdk

from routing import auth, concord, forms, universal, user

sentry_sdk.init(
    dsn=settings.sentry_url,
    send_default_pii=True,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)


@asynccontextmanager
async def lifespan(_apps: FastAPI):
    try:
        yield
    finally:
        await session_manager.close_session()

app = FastAPI(lifespan=lifespan)
app.include_router(universal.app_univers)
app.include_router(auth.app_auth)
app.include_router(concord.app_concord)
app.include_router(forms.app_forms)
app.include_router(user.app_user)

application = ASGIMiddleware(app)

app.mount("/static", StaticFiles(directory="src/static"), name="static")
scheduler = AsyncIOScheduler()


if __name__ == "__main__":
    try:
        if platform.system() == "Windows":
            uvicorn.run(
                app,
                host="127.0.0.1",
                port=settings.app_port,
                log_config="src/logs/log_config.json",
                use_colors=True,
                log_level="info",
                loop="asyncio",
            )
        else:
            uvicorn.run(
                app,
                host="0.0.0.0",
                port=settings.app_port,
                log_config="src/logs/log_config.json",
                use_colors=True,
                log_level="info",
                loop="asyncio",
            )
    except Exception as e:
        logger.error(f"Error launch app: {e}")
