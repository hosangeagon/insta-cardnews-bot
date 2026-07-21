# =============================================
# groq_client.py — Groq LLM 호출 공용 함수
# news_bot.py의 검증된 패턴(모델 fallback + 한국어 강제 재시도) 재사용
# =============================================

import re
import requests
from config import GROQ_API_KEY

MODEL_PRIMARY = "llama-3.3-70b-versatile"
MODEL_FALLBACK = "llama-3.1-8b-instant"


def 일본어_포함여부(텍스트):
    for 문자 in 텍스트:
        코드 = ord(문자)
        if 0x3040 <= 코드 <= 0x309F or 0x30A0 <= 코드 <= 0x30FF:
            return True
    return False


def 씽크태그_제거(텍스트):
    return re.sub(r"<think>.*?</think>", "", 텍스트, flags=re.DOTALL).strip()


def _호출(messages, model, max_tokens):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    응답 = requests.post(url, headers=headers, json=payload, timeout=60)
    데이터 = 응답.json()

    if "choices" not in 데이터:
        print(f"[Groq 오류] 모델={model} | {데이터}")
        return None

    return 데이터["choices"][0]["message"]["content"]


def 한국어_완성(system_prompt, user_prompt, max_tokens=1200, max_tokens_fallback=900):
    """한국어 응답을 강제하며 Groq를 호출합니다.
    - 모델 fallback: llama-3.3-70b → llama-3.1-8b
    - 일본어(히라가나/카타카나) 감지 시 최대 3회 재시도
    - 두 모델 모두 실패하면 None 반환
    """
    messages = [
        {"role": "system", "content": system_prompt + " 응답은 반드시 순수 한국어로만 작성합니다."},
        {"role": "user", "content": user_prompt},
    ]

    결과 = None
    for 시도 in range(3):
        결과 = _호출(messages, MODEL_PRIMARY, max_tokens)

        if 결과 is None:
            print("  [fallback] llama-3.3-70b 실패 → llama-3.1-8b 시도 중...")
            결과 = _호출(messages, MODEL_FALLBACK, max_tokens_fallback)

        if 결과 is None:
            return None

        결과 = 씽크태그_제거(결과)

        if not 일본어_포함여부(결과):
            if 시도 > 0:
                print(f"  → {시도 + 1}회 시도 후 한국어 응답 확보 완료")
            return 결과

        print(f"  [경고] 일본어 감지 — 재시도 중 ({시도 + 1}/3)...")

    print("  [경고] 3회 시도 후에도 일본어 포함. 마지막 결과를 사용합니다.")
    return 결과
