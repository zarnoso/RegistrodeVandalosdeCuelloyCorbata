from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os

from app.api.routes import router as politicos_router
from app.api.source_routes import router as sources_router
from app.core.database import engine, Base
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
app.include_router(sources_router, prefix="/api", tags=["Fuentes"])


@app.get("/")
def root():
    frontend_index = os.path.join(frontend_path, "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    return {
        "message": "Chile Transparente API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "mode": "demo" if os.environ.get("DEMO_MODE", "").lower() == "true" else "production",
    }


# Serve frontend
@app.get("/index.html")
async def serve_frontend():
    frontend_index = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    return {"error": "Frontend no encontrado"}
