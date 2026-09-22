# =========================================================
# Supabase 데이터베이스 연결
# =========================================================

# 환경변수를 읽기 위한 라이브러리
import os

# .env 파일을 읽기 위한 라이브러리
from dotenv import load_dotenv

# Supabase 연결 라이브러리
from supabase import create_client, Client


# .env 파일의 환경변수 불러오기
load_dotenv()


# Supabase 접속정보 가져오기
SUPABASE_URL = os.getenv("SUPABASE_URL")

SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY"
)


# Supabase URL 확인
if not SUPABASE_URL:
    raise ValueError(
        "SUPABASE_URL이 설정되지 않았습니다."
    )


# Supabase Service Role Key 확인
if not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError(
        "SUPABASE_SERVICE_ROLE_KEY가 설정되지 않았습니다."
    )


# Supabase 연결 객체 생성
# 다른 파일에서는 이 객체를 import하여 DB 사용
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)