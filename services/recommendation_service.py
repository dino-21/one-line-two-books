# =========================================================
# 책 추천 처리  (쉬운 버전) - 이 서비스의 핵심 기능
# =========================================================
#
# 전체 흐름 (5단계)
#   1) 한 줄 일기를 가져온다 (내 일기가 맞는지 확인)
#   2) 일기에 저장된 검색어 2개로 카카오에서 책을 찾는다
#        - support_keyword     → 공감되는 책
#        - perspective_keyword → 다른 관점의 책
#   3) 찾은 책을 books 테이블에 저장한다 (같은 책은 재사용)
#   4) recommendations 테이블에 추천 2건을 저장한다
#   5) 저장한 추천 결과(책 정보 포함)를 돌려준다
#
#   ※ 추천 이유는 AI를 또 부르지 않고,
#     감정/주제를 이용해 간단한 문장으로 만든다.
# =========================================================

from fastapi import HTTPException

from database import supabase
from services.diary_service import get_owned_diary
from services.kakao_book_service import search_one_book


# 추천 유형 값 (DB의 CHECK 제약과 반드시 같아야 함)
#   support     : 공감되는 책
#   perspective : 다른 관점의 책
TYPE_SUPPORT = "support"
TYPE_OPPOSITE = "perspective"


# ---------------------------------------------------------
# 책 한 권을 books 테이블에 저장하고 id를 돌려준다
#   - 같은 ISBN 책이 이미 있으면 저장하지 않고 그 id를 재사용
# ---------------------------------------------------------
def save_book(book: dict) -> int:

    isbn = book.get("isbn", "")

    # 1) 이미 있는 책인지 확인 (ISBN으로)
    if isbn:
        found = (
            supabase
            .table("books")
            .select("id")
            .eq("isbn", isbn)
            .execute()
        )
        if found.data:
            return found.data[0]["id"]  # 있으면 그대로 사용

    # 2) 새 책이면 저장하고 새 id를 돌려준다
    saved = (
        supabase
        .table("books")
        .insert({
            "isbn": isbn,
            "title": book.get("title", ""),
            "authors": book.get("authors", []),
            "publisher": book.get("publisher", ""),
            "thumbnail": book.get("thumbnail", ""),
            "contents": book.get("contents", ""),
            "book_url": book.get("book_url", ""),
        })
        .execute()
    )
    return saved.data[0]["id"]


# ---------------------------------------------------------
# 추천 이유 문장 만들기 (AI 대신 간단한 파이썬 문장)
# ---------------------------------------------------------
def make_reason(rec_type: str, emotion: str, topic: str) -> str:

    if rec_type == TYPE_SUPPORT:
        # 공감 책 이유
        if emotion:
            return f"지금의 '{emotion}' 마음에 공감해 줄 수 있는 책이에요."
        return "지금의 마음에 공감해 줄 수 있는 책이에요."

    # 다른 관점 책 이유
    if topic:
        return f"'{topic}'을(를) 다른 시각에서 바라보게 해 주는 책이에요."
    return "조금 다른 시각을 열어 줄 수 있는 책이에요."


# ---------------------------------------------------------
# 추천 만들기 (한 줄 일기 → 책 2권 추천 & 저장)
# ---------------------------------------------------------
def create_recommendations(user_id: int, diary_id: int) -> dict:

    # (1) 내 일기 가져오기 (없거나 남의 것이면 여기서 예외 발생)
    diary = get_owned_diary(user_id, diary_id)

    # 일기에 저장돼 있던 검색어 2개
    support_keyword = diary["support_keyword"]
    perspective_keyword = diary["perspective_keyword"]

    # (2) 카카오에서 책 검색 (공감 책 / 다른 관점 책)
    support_book = search_one_book(support_keyword)

    # 다른 관점 책은, 공감 책과 '같은 책'이 나오지 않도록 제외하고 검색
    #   (recommendations 테이블에 같은 (일기, 책) 조합을 못 넣게
    #    UNIQUE 제약이 걸려 있기 때문)
    exclude = support_book["isbn"] if support_book else ""
    opposite_book = search_one_book(
        perspective_keyword, exclude_isbn=exclude
    )

    # 둘 다 못 찾으면 추천할 수 없음
    if not support_book and not opposite_book:
        raise HTTPException(
            status_code=502,
            detail="카카오 도서 검색 결과가 없습니다.",
        )

    # (3~4) 같은 일기의 이전 추천은 지우고 새로 저장한다
    #        (여러 번 추천해도 중복이 쌓이지 않게)
    supabase.table("recommendations").delete().eq(
        "diary_id", diary_id
    ).execute()

    # 돌려줄 추천 목록
    result_list = []

    # 공감 책 저장
    if support_book:
        book_id = save_book(support_book)
        reason = make_reason(
            TYPE_SUPPORT, diary["emotion"], diary["topic"]
        )
        rec = (
            supabase
            .table("recommendations")
            .insert({
                "diary_id": diary_id,
                "book_id": book_id,
                "recommendation_type": TYPE_SUPPORT,
                "reason": reason,
            })
            .execute()
        )
        saved = rec.data[0]
        saved["book"] = support_book       # 응답에 책 정보도 함께
        result_list.append(saved)

    # 다른 관점 책 저장
    if opposite_book:
        book_id = save_book(opposite_book)
        reason = make_reason(
            TYPE_OPPOSITE, diary["emotion"], diary["topic"]
        )
        rec = (
            supabase
            .table("recommendations")
            .insert({
                "diary_id": diary_id,
                "book_id": book_id,
                "recommendation_type": TYPE_OPPOSITE,
                "reason": reason,
            })
            .execute()
        )
        saved = rec.data[0]
        saved["book"] = opposite_book
        result_list.append(saved)

    # (5) 결과 돌려주기
    return {
        "message": "책 추천 성공",
        "diary_id": diary_id,
        "recommendations": result_list,
    }


# ---------------------------------------------------------
# 저장된 추천 조회 (책 정보 함께)
# ---------------------------------------------------------
def get_recommendations(user_id: int, diary_id: int) -> dict:

    # 내 일기인지 확인
    get_owned_diary(user_id, diary_id)

    # recommendations + books 를 한 번에 조회 (외래키로 연결된 책 정보 포함)
    result = (
        supabase
        .table("recommendations")
        .select("*, books(*)")
        .eq("diary_id", diary_id)
        .order("id")
        .execute()
    )

    return {
        "message": "추천 목록 조회 성공",
        "diary_id": diary_id,
        "count": len(result.data),
        "recommendations": result.data,
    }
