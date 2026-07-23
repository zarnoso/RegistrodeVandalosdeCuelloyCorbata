from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.routes import router as politicos_router
from app.core.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Chile Transparente API",
    description="API para el Radar de Transparencia Política de Chile",
    version="1.0.0"
)

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
def health():
    return {"status": "healthy"}


# Serve frontend
@app.get("/index.html")
async def serve_frontend():
    from fastapi.responses import FileResponse
    frontend_index = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
    if os.path.exists(frontend_index):
        return FileResponse(frontend_index)
    return {"error": "Frontend no encontrado"}
