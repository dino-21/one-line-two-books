# =========================================================
# 회원가입 및 로그인 실제 처리
# =========================================================

import bcrypt

from fastapi import HTTPException

from database import supabase
from dependencies.auth import create_access_token


# ---------------------------------------------------------
# 회원가입 처리
# ---------------------------------------------------------
def signup_user(login_id: str, password: str):

    try:
        # 같은 로그인 아이디가 있는지 확인
        existing_user = (
            supabase
            .table("users")
            .select("id")
            .eq("login_id", login_id)
            .execute()
        )

        # 이미 가입된 아이디인 경우
        if existing_user.data:
            raise HTTPException(
                status_code=409,
                detail="이미 사용 중인 아이디입니다."
            )

        # 비밀번호를 bytes로 변환
        password_bytes = password.encode("utf-8")

        # BCrypt는 최대 72바이트까지 처리 가능
        if len(password_bytes) > 72:
            raise HTTPException(
                status_code=400,
                detail="비밀번호가 너무 깁니다."
            )

        # 비밀번호 BCrypt 암호화
        password_hash = bcrypt.hashpw(
            password_bytes,
            bcrypt.gensalt()
        ).decode("utf-8")

        # 회원정보 DB 저장
        result = (
            supabase
            .table("users")
            .insert({
                "login_id": login_id,
                "password_hash": password_hash
            })
            .execute()
        )

        # 저장 결과 확인
        if not result.data:
            raise HTTPException(
                status_code=500,
                detail="회원정보가 저장되지 않았습니다."
            )

        saved_user = result.data[0]

        # 비밀번호를 제외한 정보만 반환
        return {
            "message": "회원가입 성공",
            "user": {
                "id": saved_user["id"],
                "login_id": saved_user["login_id"],
                "created_at": saved_user["created_at"]
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"회원가입 실패: {str(e)}"
        )


# ---------------------------------------------------------
# 로그인 처리
# ---------------------------------------------------------
def login_user(login_id: str, password: str):

    try:
        # 로그인 아이디로 회원 조회
        result = (
            supabase
            .table("users")
            .select(
                "id, login_id, password_hash, created_at"
            )
            .eq("login_id", login_id)
            .execute()
        )

        # 아이디가 존재하지 않는 경우
        if not result.data:
            raise HTTPException(
                status_code=401,
                detail=(
                    "아이디 또는 비밀번호가 "
                    "올바르지 않습니다."
                )
            )

        saved_user = result.data[0]

        # 입력 비밀번호와 저장된 해시값 비교
        password_matched = bcrypt.checkpw(
            password.encode("utf-8"),
            saved_user["password_hash"].encode("utf-8")
        )

        # 비밀번호가 틀린 경우
        if not password_matched:
            raise HTTPException(
                status_code=401,
                detail=(
                    "아이디 또는 비밀번호가 "
                    "올바르지 않습니다."
                )
            )

        # 로그인 성공 시 JWT 발급
        access_token = create_access_token(
            user_id=saved_user["id"],
            login_id=saved_user["login_id"]
        )

        return {
            "message": "로그인 성공",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": saved_user["id"],
                "login_id": saved_user["login_id"]
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"로그인 실패: {str(e)}"
        )