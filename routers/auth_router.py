# =========================================================
# 회원가입, 로그인, 사용자 확인 API 주소
# =========================================================

from fastapi import APIRouter, Depends

from schemas import UserSignup, UserLogin
from services.auth_service import (
    signup_user,
    login_user
)
from dependencies.auth import get_current_user


# 인증 관련 API Router 생성
router = APIRouter(
    prefix="/auth",
    tags=["인증"]
)


# ---------------------------------------------------------
# 회원가입 API
# POST /auth/signup
# ---------------------------------------------------------
@router.post("/signup", status_code=201)
def signup(user: UserSignup):

    return signup_user(
        login_id=user.login_id,
        password=user.password
    )


# ---------------------------------------------------------
# 로그인 API
# POST /auth/login
# ---------------------------------------------------------
@router.post("/login")
def login(user: UserLogin):

    return login_user(
        login_id=user.login_id,
        password=user.password
    )


# ---------------------------------------------------------
# 현재 로그인 사용자 확인 API
# GET /auth/me
# ---------------------------------------------------------
@router.get("/me")
def get_my_information(
    current_user: dict = Depends(get_current_user)
):

    return {
        "message": "인증된 사용자입니다.",
        "user": current_user
    }