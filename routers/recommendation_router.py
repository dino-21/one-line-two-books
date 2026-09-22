# =========================================================
# 책 추천 API 주소
# =========================================================
#
# 모든 API는 로그인(JWT)이 필요하다.
#   POST /recommendations              추천 생성 (책 두 권 추천 & 저장)
#   GET  /recommendations/{diary_id}   특정 일기의 저장된 추천 조회
# =========================================================

from fastapi import APIRouter, Depends

from schemas import RecommendationCreate
from dependencies.auth import get_current_user
from services.recommendation_service import (
    create_recommendations,
    get_recommendations
)


# 추천 관련 API Router 생성
router = APIRouter(
    prefix="/recommendations",
    tags=["책 추천"]
)


# ---------------------------------------------------------
# 추천 생성
# POST /recommendations
# body: { "diary_id": 1 }
# ---------------------------------------------------------
@router.post("", status_code=201)
def create(
    body: RecommendationCreate,
    current_user: dict = Depends(get_current_user)
):

    return create_recommendations(
        user_id=current_user["id"],
        diary_id=body.diary_id
    )


# ---------------------------------------------------------
# 특정 일기의 저장된 추천 조회
# GET /recommendations/{diary_id}
# ---------------------------------------------------------
@router.get("/{diary_id}")
def read(
    diary_id: int,
    current_user: dict = Depends(get_current_user)
):

    return get_recommendations(
        user_id=current_user["id"],
        diary_id=diary_id
    )
