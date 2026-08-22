from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import agent, cases, onboarding
from app.core.config import get_settings

settings = get_settings()

# Populated by the Docker build (see /Dockerfile), which copies the built
# Vite frontend here so this one service can serve both the API and the
# app — no separate frontend host, no CORS between them. Absent in local
# `uvicorn --reload` dev, where the Vite dev server runs separately.
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(
    title="DragonPath API",
    description=(
        "Deadline-aware visa preparation workspace API for international "
        "students in Korea. See /기능 정의 docs D-06..D-09 for product spec."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(onboarding.router)
app.include_router(cases.router)
app.include_router(agent.router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        """SPA fallback: any non-API path returns index.html so React
        Router can handle client-side routes like /cases/:id directly.
        """
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        candidate = STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html")
