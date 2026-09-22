# =========================================================
# 카카오 도서 검색 API 서비스
# =========================================================
#
# 이 파일이 하는 일
#   - 검색어(키워드)를 받아 카카오 도서 API로 책을 찾는다.
#   - 검색 결과 중 가장 관련도 높은 책 한 권만 골라
#     우리 서비스에서 쓰기 좋은 형태로 정리해서 돌려준다.
#
# 참고: 카카오 도서 검색 API 문서
#   https://developers.kakao.com/docs/latest/ko/daum-search/dev-guide
# =========================================================

import os

import httpx

from dotenv import load_dotenv


# .env 환경변수 불러오기
load_dotenv()


# 카카오 REST API 키 가져오기
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")


# 카카오 키 확인
if not KAKAO_REST_API_KEY:
    raise ValueError(
        "KAKAO_REST_API_KEY가 설정되지 않았습니다."
    )


# 카카오 도서 검색 주소
KAKAO_BOOK_URL = "https://dapi.kakao.com/v3/search/book"


# ---------------------------------------------------------
# 키워드로 책 한 권 검색하기
# ---------------------------------------------------------
def search_one_book(keyword: str, exclude_isbn: str = "") -> dict | None:
    """
    검색어로 카카오 도서 API를 호출하고
    가장 관련도 높은 책 한 권을 정리해서 돌려준다.

    exclude_isbn 을 주면 그 책은 건너뛴다.
    (같은 책이 두 번 추천되는 것을 막기 위함)

    반환 예시
    {
        "isbn": "8996991341 9788996991342",
        "title": "미움받을 용기",
        "authors": ["기시미 이치로", "고가 후미타케"],
        "publisher": "인플루엔셜",
        "thumbnail": "https://...",
        "contents": "책 소개 일부...",
        "book_url": "https://..."
    }

    검색 결과가 없으면 None을 돌려준다.
    """

    # 카카오 인증 헤더 (KakaoAK + REST API 키)
    headers = {
        "Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"
    }

    # 검색 조건
    #   query : 검색어
    #   size  : 여러 권을 받아두고, 그 중에서 한 권을 고른다
    #   sort  : accuracy(정확도) / latest(최신)
    params = {
        "query": keyword,
        "size": 10,
        "sort": "accuracy"
    }

    try:
        # 카카오 도서 API 호출
        response = httpx.get(
            KAKAO_BOOK_URL,
            headers=headers,
            params=params,
            timeout=10.0
        )

        # HTTP 오류(401, 429 등)면 예외 발생
        response.raise_for_status()

        # 응답(JSON) → 딕셔너리
        data = response.json()

        # 검색된 책 목록
        documents = data.get("documents", [])

        # 검색 결과가 없으면 None
        if not documents:
            return None

        # 정확도순으로 살펴보며, 제외할 책(exclude_isbn)이 아니면 선택
        book = None
        for doc in documents:
            if exclude_isbn and doc.get("isbn", "") == exclude_isbn:
                continue          # 같은 책이면 건너뛰기
            book = doc
            break

        # 쓸 만한 책이 없으면 None
        if book is None:
            return None

        # 우리 DB(books 테이블) 형식에 맞게 정리
        return {
            "isbn": book.get("isbn", ""),
            "title": book.get("title", ""),
            "authors": book.get("authors", []),
            "publisher": book.get("publisher", ""),
            "thumbnail": book.get("thumbnail", ""),
            "contents": book.get("contents", ""),
            "book_url": book.get("url", "")
        }

    except Exception:
        # 네트워크 오류 등으로 검색 실패 시 None
        return None
