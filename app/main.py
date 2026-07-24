from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.orm import Session
import os

from app.api.routes import router as politicos_router
from app.core.database import engine, Base, get_db
from app.core.limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crea tablas al arrancar la app (no al importar el módulo, para poder testear)."""
    Base.metadata.create_all(bind=engine)
    yield


# Create FastAPI app
app = FastAPI(
    title="Chile Transparente API",
    description="API para el Radar de Transparencia Política de Chile",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# CORS: API pública de solo lectura, sin auth por cookies -> no se necesitan credentials.
# allow_origins=["*"] + allow_credentials=True es inválido para navegadores (rechazado por spec).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# Include routers
app.include_router(politicos_router, prefix="/api/politicos", tags=["Políticos"])


@app.get("/")
def root():
    return {
        "message": "Chile Transparente API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {e}")


# Serve frontend
@app.get("/index.html")
async def serve_frontend():
    from fastapi.responses import FileResponse
    frontend_index = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    return {"error": "Frontend no encontrado"}
