# =========================================================
# OpenAI로 "한 줄 일기" 분석하기  (쉬운 버전)
# =========================================================
#
# 이 파일이 하는 일 (딱 하나!)
#   한 줄 일기 문장을 OpenAI에게 보내서
#   아래 5가지를 한 번에 받아온다.
#     - emotion              : 감정
#     - topic                : 주제
#     - viewpoint            : 글쓴이의 관점(입장)
#     - support_keyword      : 공감해 주는 책을 찾을 검색어
#     - perspective_keyword  : 다른 관점의 책을 찾을 검색어
#
#   ※ OpenAI 호출은 딱 1번만 한다. (그래서 빠르고 저렴하다)
# =========================================================

import os
import json

from dotenv import load_dotenv
from openai import OpenAI


# .env 파일의 환경변수 불러오기
load_dotenv()


# OpenAI 키와 사용할 모델
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# 키가 없으면 서버 시작 단계에서 바로 알려 준다
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")


# OpenAI 연결 객체 (파일에서 한 번만 만든다)
client = OpenAI(api_key=OPENAI_API_KEY)


# ---------------------------------------------------------
# 한 줄 일기 분석하기
# ---------------------------------------------------------
def analyze_diary(content: str) -> dict:

    # AI에게 줄 지시문
    # "이런 항목들을 JSON으로만 답해줘" 라고 부탁하는 부분
    system_prompt = (
        "너는 한국어 문장을 분석하는 도우미다. "
        "사용자의 '한 줄 일기'를 읽고 아래 5가지를 "
        "반드시 JSON 형식으로만 답한다.\n"
        "- emotion: 문장에서 느껴지는 감정 (짧게)\n"
        "- topic: 문장의 핵심 주제 (짧게)\n"
        "- viewpoint: 글쓴이의 관점/입장 (한 문장)\n"
        "- support_keyword: 글쓴이에게 '공감·위로'가 될 책을 "
        "찾기 위한 도서 검색어 (한두 단어)\n"
        "- perspective_keyword: 글쓴이와 '다른 관점'을 보여 줄 "
        "책을 찾기 위한 도서 검색어 (한두 단어)"
    )

    try:
        # OpenAI 호출 (JSON으로 답하도록 설정)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            response_format={"type": "json_object"},
        )

        # AI가 준 JSON 문자열을 파이썬 딕셔너리로 변환
        result = json.loads(response.choices[0].message.content)

        # 혹시 빠진 값이 있어도 안전하도록 기본값을 채워 준다
        return {
            "emotion": result.get("emotion", ""),
            "topic": result.get("topic", ""),
            "viewpoint": result.get("viewpoint", ""),
            "support_keyword": result.get("support_keyword", content),
            "perspective_keyword": result.get(
                "perspective_keyword", content
            ),
        }

    except Exception:
        # AI 호출이 실패해도 서버가 멈추지 않도록
        # 최소한 원문을 검색어로 사용한다
        return {
            "emotion": "",
            "topic": "",
            "viewpoint": "",
            "support_keyword": content,
            "perspective_keyword": content,
        }
