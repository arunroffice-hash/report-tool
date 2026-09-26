from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.inventory import router as inventory_router
from app.api.routes.logs import router as logs_router
from app.api.routes.reports import router as reports_router
from app.api.routes.variance import router as variance_router
from app.core.config import settings
from app.core.database import create_db_and_tables, seed_admin_user

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

app.include_router(auth_router)
app.include_router(inventory_router)
app.include_router(logs_router)
app.include_router(reports_router)
app.include_router(variance_router)


@app.on_event("startup")
async def startup_event() -> None:
    """Create tables and seed the default admin user on application startup."""
    create_db_and_tables()
    seed_admin_user()


@app.get("/")
async def root(request: Request) -> RedirectResponse:
    """Root route redirects users to the application login or reports page."""
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=302)
    return RedirectResponse(url="/reports", status_code=302)


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
