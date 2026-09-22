# =========================================================
# JWT 생성 및 인증 검사
# =========================================================

import os
from datetime import datetime, timedelta, timezone

import jwt

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)


# .env 환경변수 불러오기
load_dotenv()


# JWT 설정
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "60")
)


# JWT 비밀키 확인
if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY가 설정되지 않았습니다."
    )


# Authorization 헤더의 Bearer 토큰을 받기 위한 설정
security = HTTPBearer()


# ---------------------------------------------------------
# JWT 액세스 토큰 생성
# ---------------------------------------------------------
def create_access_token(
    user_id: int,
    login_id: str
) -> str:

    # 현재 UTC 시간
    now = datetime.now(timezone.utc)

    # JWT에 저장할 데이터
    payload = {
        # 로그인한 회원번호
        "sub": str(user_id),

        # 로그인 아이디
        "login_id": login_id,

        # 토큰 발급시간
        "iat": now,

        # 토큰 만료시간
        "exp": now + timedelta(
            minutes=JWT_EXPIRE_MINUTES
        )
    }

    # JWT 문자열 생성
    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


# ---------------------------------------------------------
# JWT를 검사하고 현재 로그인 사용자 반환
# ---------------------------------------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    )
):
    try:
        # Authorization 헤더에서 JWT 가져오기
        token = credentials.credentials

        # JWT 서명과 만료시간 검사
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        # JWT에 저장된 회원정보 가져오기
        user_id = payload.get("sub")
        login_id = payload.get("login_id")

        # 회원정보가 없으면 인증 실패
        if not user_id or not login_id:
            raise HTTPException(
                status_code=401,
                detail="유효하지 않은 인증정보입니다."
            )

        return {
            "id": int(user_id),
            "login_id": login_id
        }

    # JWT 사용시간이 만료된 경우
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="로그인 시간이 만료되었습니다."
        )

    # JWT가 변조되었거나 잘못된 경우
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 토큰입니다."
        )

    # 회원번호 형식이 잘못된 경우
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="유효하지 않은 인증정보입니다."
        )