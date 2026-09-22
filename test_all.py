# =========================================================
# 전체 기능 한번에 테스트하는 스크립트
# =========================================================
#
# 이 스크립트는 실행 중인 서버(http://localhost:8000)에 대고
# 회원가입 → 로그인 → 일기 작성 → 책 추천 → 조회 → 수정 → 삭제
# 까지 전체 흐름을 순서대로 실행하며 결과를 출력한다.
#
# 실행 방법
#   1) 로컬 테스트: 다른 터미널에서 서버를 켠 뒤 실행
#        uvicorn main:app --reload
#        python test_all.py
#
#   2) Render(배포 주소) 테스트: 주소를 인자나 환경변수로 전달
#        python test_all.py https://내앱이름.onrender.com
#      또는
#        BASE_URL=https://내앱이름.onrender.com python test_all.py
# =========================================================

import os
import sys
import random

import httpx


# 테스트 대상 서버 주소
#   우선순위: 실행 인자 > 환경변수 BASE_URL > 기본값(localhost)
BASE_URL = (
    (sys.argv[1] if len(sys.argv) > 1 else None)
    or os.getenv("BASE_URL")
    or "http://localhost:8000"
)

# 테스트용 계정 (매번 새 아이디를 만들기 위해 랜덤 숫자 사용)
TEST_LOGIN_ID = "tester" + str(random.randint(1000, 9999))
TEST_PASSWORD = "test1234"


# 통과/실패 개수 세기
passed = 0
failed = 0


# ---------------------------------------------------------
# 결과를 예쁘게 출력하는 도우미 함수
# ---------------------------------------------------------
def step(title):
    print("\n" + "=" * 55)
    print("▶ " + title)
    print("=" * 55)


def check(condition, message):
    global passed, failed
    if condition:
        passed += 1
        print("  ✅ PASS -", message)
    else:
        failed += 1
        print("  ❌ FAIL -", message)


# ---------------------------------------------------------
# 테스트 시작
# ---------------------------------------------------------
def main():
    print("테스트 대상 서버:", BASE_URL)

    # httpx 클라이언트 (타임아웃 넉넉하게 - AI 호출 때문에)
    client = httpx.Client(base_url=BASE_URL, timeout=60.0)

    token = None
    diary_id = None

    # -----------------------------------------------------
    # 0. 서버 동작 확인
    # -----------------------------------------------------
    step("0. 서버 상태 확인 (/health)")
    try:
        res = client.get("/health")
        print("  응답:", res.json())
        check(res.status_code == 200, "서버가 정상 동작한다")
    except Exception as e:
        print("  서버에 연결할 수 없습니다:", e)
        print("  → 먼저 'uvicorn main:app --reload' 로 서버를 켜세요.")
        return

    # -----------------------------------------------------
    # 0-1. DB 연결 확인
    # -----------------------------------------------------
    step("0-1. Supabase 연결 확인 (/db-test)")
    res = client.get("/db-test")
    print("  응답:", res.json().get("message"))
    check(res.status_code == 200, "Supabase에 연결된다")

    # -----------------------------------------------------
    # 1. 회원가입
    # -----------------------------------------------------
    step("1. 회원가입 (POST /auth/signup)")
    res = client.post("/auth/signup", json={
        "login_id": TEST_LOGIN_ID,
        "password": TEST_PASSWORD
    })
    print("  아이디:", TEST_LOGIN_ID)
    print("  응답:", res.json())
    check(res.status_code == 201, "회원가입에 성공한다")

    # -----------------------------------------------------
    # 2. 로그인 (JWT 토큰 받기)
    # -----------------------------------------------------
    step("2. 로그인 (POST /auth/login)")
    res = client.post("/auth/login", json={
        "login_id": TEST_LOGIN_ID,
        "password": TEST_PASSWORD
    })
    data = res.json()
    check(res.status_code == 200, "로그인에 성공한다")

    if res.status_code == 200:
        token = data["access_token"]
        print("  토큰(앞 30자):", token[:30], "...")
        check(bool(token), "JWT 토큰을 받았다")

    # 이후 요청에 쓸 인증 헤더
    headers = {"Authorization": f"Bearer {token}"}

    # -----------------------------------------------------
    # 3. 내 정보 확인 (JWT 인증 테스트)
    # -----------------------------------------------------
    step("3. 내 정보 확인 (GET /auth/me)")
    res = client.get("/auth/me", headers=headers)
    print("  응답:", res.json())
    check(res.status_code == 200, "토큰으로 내 정보를 확인한다")

    # 3-1. 토큰 없이 접근하면 막히는지 확인
    res_no_token = client.get("/auth/me")
    check(
        res_no_token.status_code in (401, 403),
        "토큰 없으면 접근이 막힌다"
    )

    # -----------------------------------------------------
    # 4. 한 줄 일기 작성 (AI 분석 포함)
    # -----------------------------------------------------
    step("4. 한 줄 일기 작성 (POST /diaries)")
    res = client.post(
        "/diaries",
        headers=headers,
        json={"content": "요즘 너무 지쳐서 아무것도 하기 싫다."}
    )
    data = res.json()
    check(res.status_code == 201, "일기가 등록된다")

    if res.status_code == 201:
        diary = data["diary"]
        diary_id = diary["id"]
        print("  일기 번호:", diary_id)
        print("  감정:", diary.get("emotion"))
        print("  주제:", diary.get("topic"))
        print("  공감 키워드:", diary.get("support_keyword"))
        print("  반대 키워드:", diary.get("perspective_keyword"))
        check(
            bool(diary.get("support_keyword")),
            "AI가 공감 키워드를 만들었다"
        )
        check(
            bool(diary.get("perspective_keyword")),
            "AI가 다른 관점 키워드를 만들었다"
        )

    # -----------------------------------------------------
    # 5. 책 추천 (카카오 도서 API + 저장)
    # -----------------------------------------------------
    step("5. 책 추천 받기 (POST /recommendations)")
    res = client.post(
        "/recommendations",
        headers=headers,
        json={"diary_id": diary_id}
    )
    data = res.json()
    check(res.status_code == 201, "추천이 생성된다")

    if res.status_code == 201:
        recs = data["recommendations"]
        print("  추천 개수:", len(recs))
        for rec in recs:
            book = rec.get("book", {})
            print("   -", rec["recommendation_type"],
                  "|", book.get("title"))
            print("     이유:", rec.get("reason"))
        check(len(recs) >= 1, "책이 한 권 이상 추천된다")

    # -----------------------------------------------------
    # 6. 저장된 추천 조회
    # -----------------------------------------------------
    step("6. 저장된 추천 조회 (GET /recommendations/{diary_id})")
    res = client.get(
        f"/recommendations/{diary_id}",
        headers=headers
    )
    data = res.json()
    print("  저장된 추천 개수:", data.get("count"))
    check(res.status_code == 200, "추천이 DB에 저장되어 조회된다")

    # -----------------------------------------------------
    # 7. 일기 목록 조회
    # -----------------------------------------------------
    step("7. 내 일기 목록 조회 (GET /diaries)")
    res = client.get("/diaries", headers=headers)
    data = res.json()
    print("  일기 개수:", data.get("count"))
    check(res.status_code == 200, "일기 목록이 조회된다")

    # -----------------------------------------------------
    # 8. 일기 수정
    # -----------------------------------------------------
    step("8. 일기 수정 (PUT /diaries/{diary_id})")
    res = client.put(
        f"/diaries/{diary_id}",
        headers=headers,
        json={"content": "그래도 내일은 조금 나아지겠지."}
    )
    check(res.status_code == 200, "일기가 수정된다")

    # -----------------------------------------------------
    # 9. 일기 삭제 (연결된 추천도 함께 삭제)
    # -----------------------------------------------------
    step("9. 일기 삭제 (DELETE /diaries/{diary_id})")
    res = client.delete(
        f"/diaries/{diary_id}",
        headers=headers
    )
    print("  응답:", res.json())
    check(res.status_code == 200, "일기가 삭제된다")

    client.close()

    # -----------------------------------------------------
    # 최종 결과
    # -----------------------------------------------------
    print("\n" + "=" * 55)
    print(f"  테스트 종료 →  성공 {passed}건 / 실패 {failed}건")
    print("=" * 55)


if __name__ == "__main__":
    main()
