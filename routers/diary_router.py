# =========================================================
# 한 줄 일기 API 주소
# =========================================================
#
# 모든 API는 로그인(JWT)이 필요하다.
#   POST   /diaries        일기 등록
#   GET    /diaries        내 일기 목록
#   GET    /diaries/{id}   일기 한 개 조회
#   PUT    /diaries/{id}   일기 수정
#   DELETE /diaries/{id}   일기 삭제
# =========================================================

from fastapi import APIRouter, Depends

from schemas import DiaryCreate, DiaryUpdate
from dependencies.auth import get_current_user
from services.diary_service import (
    create_diary,
    list_diaries,
    get_diary,
    update_diary,
    delete_diary
)


# 일기 관련 API Router 생성
router = APIRouter(
    prefix="/diaries",
    tags=["한 줄 일기"]
)


# ---------------------------------------------------------
# 한 줄 일기 등록
# POST /diaries
# ---------------------------------------------------------
@router.post("", status_code=201)
def create(
    diary: DiaryCreate,
    current_user: dict = Depends(get_current_user)
):

    return create_diary(
        user_id=current_user["id"],
        content=diary.content
    )


# ---------------------------------------------------------
# 내 일기 목록 조회
# GET /diaries
# ---------------------------------------------------------
@router.get("")
def read_list(
    current_user: dict = Depends(get_current_user)
):

    return list_diaries(
        user_id=current_user["id"]
    )


# ---------------------------------------------------------
# 일기 한 개 조회
# GET /diaries/{diary_id}
# ---------------------------------------------------------
@router.get("/{diary_id}")
def read_one(
    diary_id: int,
    current_user: dict = Depends(get_current_user)
):

    return get_diary(
        user_id=current_user["id"],
        diary_id=diary_id
    )


# ---------------------------------------------------------
# 일기 수정
# PUT /diaries/{diary_id}
# ---------------------------------------------------------
@router.put("/{diary_id}")
def update(
    diary_id: int,
    diary: DiaryUpdate,
    current_user: dict = Depends(get_current_user)
):

    return update_diary(
        user_id=current_user["id"],
        diary_id=diary_id,
        content=diary.content
    )


# ---------------------------------------------------------
# 일기 삭제
# DELETE /diaries/{diary_id}
# ---------------------------------------------------------
@router.delete("/{diary_id}")
def delete(
    diary_id: int,
    current_user: dict = Depends(get_current_user)
):

    return delete_diary(
        user_id=current_user["id"],
        diary_id=diary_id
    )
