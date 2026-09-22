# =========================================================
# 한 줄 일기 처리  (쉬운 버전)
# =========================================================
#
# 이 파일이 하는 일
#   - 한 줄 일기를 등록 / 목록조회 / 수정 / 삭제 한다.
#   - 등록·수정할 때 AI로 문장을 분석해서
#     감정/주제/관점/검색어 2개를 함께 저장한다.
#   - 항상 "내 일기"만 다루도록 확인한다.
# =========================================================

from fastapi import HTTPException

from database import supabase
from services.ai_service import analyze_diary


# ---------------------------------------------------------
# 내 일기인지 확인하고 가져오기
#   (다른 서비스에서도 쓰기 때문에 밑줄 없이 공개 함수로 둔다)
# ---------------------------------------------------------
def get_owned_diary(user_id: int, diary_id: int) -> dict:

    result = (
        supabase
        .table("diaries")
        .select("*")
        .eq("id", diary_id)
        .eq("user_id", user_id)   # 내 것만
        .execute()
    )

    # 내 일기가 없으면 404
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="해당 일기를 찾을 수 없습니다.",
        )

    return result.data[0]


# ---------------------------------------------------------
# 1. 한 줄 일기 등록 (AI 분석 포함)
# ---------------------------------------------------------
def create_diary(user_id: int, content: str) -> dict:

    # AI로 문장 분석 (감정/주제/관점/검색어 2개)
    analysis = analyze_diary(content)

    # diaries 테이블에 저장
    result = (
        supabase
        .table("diaries")
        .insert({
            "user_id": user_id,
            "content": content,
            "emotion": analysis["emotion"],
            "topic": analysis["topic"],
            "viewpoint": analysis["viewpoint"],
            "support_keyword": analysis["support_keyword"],
            "perspective_keyword": analysis["perspective_keyword"],
        })
        .execute()
    )

    return {
        "message": "한 줄 일기 등록 성공",
        "diary": result.data[0],
    }


# ---------------------------------------------------------
# 2. 내 일기 목록 조회 (최신순)
# ---------------------------------------------------------
def list_diaries(user_id: int) -> dict:

    result = (
        supabase
        .table("diaries")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "message": "일기 목록 조회 성공",
        "count": len(result.data),
        "diaries": result.data,
    }


# ---------------------------------------------------------
# 2-1. 일기 한 개 조회
# ---------------------------------------------------------
def get_diary(user_id: int, diary_id: int) -> dict:

    diary = get_owned_diary(user_id, diary_id)

    return {
        "message": "일기 조회 성공",
        "diary": diary,
    }


# ---------------------------------------------------------
# 3. 일기 수정 (수정한 문장을 다시 AI로 분석)
# ---------------------------------------------------------
def update_diary(user_id: int, diary_id: int, content: str) -> dict:

    # 내 일기인지 먼저 확인
    get_owned_diary(user_id, diary_id)

    # 수정한 문장을 다시 분석
    analysis = analyze_diary(content)

    result = (
        supabase
        .table("diaries")
        .update({
            "content": content,
            "emotion": analysis["emotion"],
            "topic": analysis["topic"],
            "viewpoint": analysis["viewpoint"],
            "support_keyword": analysis["support_keyword"],
            "perspective_keyword": analysis["perspective_keyword"],
        })
        .eq("id", diary_id)
        .execute()
    )

    return {
        "message": "일기 수정 성공",
        "diary": result.data[0],
    }


# ---------------------------------------------------------
# 4. 일기 삭제 (연결된 추천도 함께 삭제)
# ---------------------------------------------------------
def delete_diary(user_id: int, diary_id: int) -> dict:

    # 내 일기인지 먼저 확인
    get_owned_diary(user_id, diary_id)

    # 이 일기에 달린 추천을 먼저 지우고
    supabase.table("recommendations").delete().eq(
        "diary_id", diary_id
    ).execute()

    # 일기를 지운다
    supabase.table("diaries").delete().eq("id", diary_id).execute()

    return {
        "message": "일기 삭제 성공",
        "deleted_diary_id": diary_id,
    }
