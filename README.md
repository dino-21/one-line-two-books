# 한 줄, 두 권 📖  (쉬운 버전 · 강의용)

한 줄 일기를 남기면, **공감해 주는 책**과 **다른 관점의 책** 두 권을 추천해 주는 서비스입니다.

- 문장 분석: OpenAI (호출은 **일기당 딱 1번**)
- 책 검색: 카카오 도서 검색 API
- 로그인: JWT
- 데이터 저장: Supabase (PostgreSQL)
- 백엔드: FastAPI / 프론트: 순수 HTML·CSS·JS

> 이 버전은 학생이 흐름을 쉽게 따라가도록 만든 **쉬운 버전**입니다.
> OpenAI는 일기당 1번만 호출하고, 추천 이유는 감정/주제를 이용해
> 파이썬에서 간단한 문장으로 만듭니다. (AI를 두 번 부르지 않음)

---

## 1. 동작 흐름

```
[한 줄 일기 작성]
      ↓  OpenAI 1번 호출 → 감정·주제·관점 + 검색어 2개
[diaries 저장]
      ↓  검색어 2개로 카카오 도서 검색
[books 저장(같은 책은 재사용)]  →  [recommendations 저장]
      ↓  추천 이유는 감정/주제로 파이썬에서 생성
공감 책 1권  +  다른 관점 책 1권  추천 결과 표시
```

---

## 2. 폴더 구조

```
one-line-two-books/
├── main.py                      # FastAPI 실행 + 라우터 조립 + 프론트 제공
├── database.py                  # Supabase 연결
├── schemas.py                   # 요청 데이터 형식
├── schema.sql                   # Supabase 테이블 생성 SQL (ERD)
├── requirements.txt             # 파이썬 라이브러리 목록
├── .env.example                 # 환경변수 예시 (복사해서 .env 로 사용)
├── test_all.py                  # 전체 기능 한번에 테스트
│
├── dependencies/
│   └── auth.py                  # JWT 생성 / 검증
│
├── routers/                     # API 주소 정의
│   ├── auth_router.py           # 회원가입 / 로그인 / 내 정보
│   ├── diary_router.py          # 한 줄 일기 CRUD
│   └── recommendation_router.py # 책 추천
│
├── services/                    # 실제 처리 로직
│   ├── auth_service.py          # 회원가입 / 로그인
│   ├── diary_service.py         # 일기 처리 (AI 분석 저장)
│   ├── recommendation_service.py# 추천 처리 (핵심 기능)
│   ├── kakao_book_service.py    # 카카오 도서 검색
│   └── ai_service.py            # OpenAI 문장 분석
│
└── frontend/                    # 웹 화면
    ├── index.html
    ├── style.css
    └── app.js
```

---

## 3. 설치 및 실행 (5단계)

### 1) 라이브러리 설치

```bash
# (권장) 가상환경 만들기
python -m venv venv
source venv/bin/activate        # 윈도우: venv\Scripts\activate

# 라이브러리 설치
pip install -r requirements.txt
```

### 2) 환경변수(.env) 만들기

```bash
cp .env.example .env
```

그리고 `.env` 파일을 열어 본인 키를 채웁니다.

| 항목 | 설명 |
|------|------|
| `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` | Supabase > Settings > API |
| `JWT_SECRET_KEY` | 긴 무작위 문자열 (아래 명령으로 생성 가능) |
| `KAKAO_REST_API_KEY` | 카카오 developers > 앱 키 > REST API 키 |
| `OPENAI_API_KEY` | platform.openai.com > API keys |

JWT 비밀키 만들기:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3) Supabase 테이블 만들기

Supabase 대시보드 > **SQL Editor** 에 `schema.sql` 내용을 붙여넣고 **Run** 합니다.
(이미 테이블이 있으면 건너뛰어도 됩니다.)

### 4) 서버 실행

```bash
uvicorn main:app --reload
```

### 5) 접속

- 웹 화면: http://localhost:8000
- API 문서(Swagger): http://localhost:8000/docs

---

## 4. 전체 기능 한번에 테스트

서버를 켠 상태에서, **다른 터미널**을 열고 실행합니다.

```bash
python test_all.py
```

회원가입 → 로그인 → 일기 작성 → 책 추천 → 조회 → 수정 → 삭제까지
순서대로 실행하며 각 단계의 성공/실패를 출력합니다.

---

## 5. API 요약

| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|:---:|
| POST | `/auth/signup` | 회원가입 | |
| POST | `/auth/login` | 로그인 (JWT 발급) | |
| GET | `/auth/me` | 내 정보 확인 | ✅ |
| POST | `/diaries` | 한 줄 일기 등록 (AI 분석) | ✅ |
| GET | `/diaries` | 내 일기 목록 | ✅ |
| GET | `/diaries/{id}` | 일기 한 개 조회 | ✅ |
| PUT | `/diaries/{id}` | 일기 수정 | ✅ |
| DELETE | `/diaries/{id}` | 일기 삭제 | ✅ |
| POST | `/recommendations` | 책 두 권 추천 & 저장 | ✅ |
| GET | `/recommendations/{diary_id}` | 저장된 추천 조회 | ✅ |
| GET | `/health` | 서버 상태 확인 | |
| GET | `/db-test` | Supabase 연결 확인 | |

> ✅ 표시된 API는 요청 헤더에 `Authorization: Bearer <토큰>` 이 필요합니다.

---

## 6. 나중에 Render로 배포하기 (참고)

지금은 **로컬 실행**에 집중하면 됩니다. 배포는 나중에 아래 순서로 하면 됩니다.

1. 코드를 GitHub 저장소에 올린다. (`.env` 는 올리지 않음 — 이미 `.gitignore` 처리)
2. Render 대시보드 > **New > Blueprint** 에서 저장소를 연결하면 `render.yaml` 을 자동으로 읽습니다.
3. Render **Environment** 탭에서 키 값(`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `KAKAO_REST_API_KEY`, `OPENAI_API_KEY`)을 입력합니다.
   - `JWT_SECRET_KEY` 는 Render가 자동 생성합니다.
4. 배포되면 프론트·API가 같은 주소에서 동작합니다. (예: `https://내앱이름.onrender.com`)

배포 주소로 전체 테스트도 가능합니다.

```bash
python test_all.py https://내앱이름.onrender.com
```

---

## 7. 참고

- `recommendation_type` 값은 `support`(공감 관점), `opposite`(다른 관점) 두 가지입니다.
- `.env` 파일은 절대 외부에 공개하지 마세요. (`.gitignore` 에 이미 포함)
- 같은 일기로 다시 추천받으면, 이전 추천은 지우고 새로 저장합니다.
