
# =========================================================
# FastAPI 애플리케이션 실행 및 Router 조립
# =========================================================

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import supabase
from routers.auth_router import router as auth_router
from routers.diary_router import router as diary_router
from routers.recommendation_router import (
    router as recommendation_router
)


# FastAPI 애플리케이션 생성
app = FastAPI(
    title="한 줄, 두 권",
    description=(
        "한 줄을 입력하면 서로 다른 관점의 "
        "책 두 권을 추천하는 서비스"
    ),
    version="1.0.0"
)


# ---------------------------------------------------------
# CORS 설정
# 프론트엔드(브라우저)에서 API를 호출할 수 있도록 허용
# 수업/실습 편의를 위해 모든 출처를 허용한다.
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ---------------------------------------------------------
# Router 등록 (인증 / 한 줄 일기 / 책 추천)
# ---------------------------------------------------------
app.include_router(auth_router)
app.include_router(diary_router)
app.include_router(recommendation_router)


# ---------------------------------------------------------
# FastAPI 서버 동작 확인
# ---------------------------------------------------------
@app.get("/health", tags=["서버 확인"])
def health_check():

    return {
        "status": "ok",
        "message": "FastAPI 서버 정상 동작"
    }


# ---------------------------------------------------------
# FastAPI와 Supabase 연결 확인
# ---------------------------------------------------------
@app.get("/db-test", tags=["서버 확인"])
def database_test():

    try:
        result = (
            supabase
            .table("users")
            .select("id, login_id, created_at")
            .execute()
        )

        return {
            "status": "success",
            "message": "Supabase 연결 성공",
            "data": result.data
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Supabase 연결 실패: {str(e)}"
        )


# ---------------------------------------------------------
# 프론트엔드(정적 파일) 서비스
# http://localhost:8000/ 로 접속하면 웹 화면이 열린다.
#   * API 경로(/auth, /diaries 등)보다 뒤에 등록해야
#     API가 정상 동작한다.
# ---------------------------------------------------------
FRONTEND_DIR = os.path.join(
    os.path.dirname(__file__),
    "frontend"
)

app.mount(
    "/",
    StaticFiles(directory=FRONTEND_DIR, html=True),
    name="frontend"
)
