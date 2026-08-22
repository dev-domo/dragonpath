from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import agent, cases, onboarding
from app.core.config import get_settings

settings = get_settings()

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
