from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import boards, lists, cards

app = FastAPI(
    title="칸반 보드 API",
    description="팀 공유 칸반 보드 백엔드 (Supabase + FastAPI)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(boards.router)
app.include_router(lists.router)
app.include_router(cards.router)


@app.get("/")
def root():
    return {"message": "칸반 보드 API 서버 실행 중", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
