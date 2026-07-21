# =============================================
# caption_hashtags.py — STEP7: 인스타그램 캡션·해시태그 생성
#
# [지시사항]
# 1. 캡션은 3~5문장, 핵심 요약을 자연스럽게 풀어씀
# 2. 마지막 줄에 "자세한 내용은 원본 영상을 확인하세요" + 채널명 표기
# 3. 해시태그 10~15개, 대중적 태그 + 세부 주제 태그 혼합
# 4. 과장/자극적 표현, 이모지 사용 금지
# =============================================

import json

from groq_client import 한국어_완성


def 캡션_해시태그_생성(요약, 채널명, url):
    summary = 요약.get("summary", "")
    points = 요약.get("points", [])

    system_prompt = "당신은 인스타그램 게시물의 캡션과 해시태그를 작성하는 콘텐츠 담당자입니다."
    user_prompt = f"""아래 카드뉴스 요약 내용을 바탕으로 인스타그램 캡션과 해시태그를 작성하세요.

핵심 요약: {summary}
포인트: {" / ".join(p for p in points if p)}
채널명: {채널명}
URL: {url}

[지시사항]
1. 캡션은 3~5문장, 카드뉴스 핵심 요약을 자연스럽게 풀어 쓰세요.
2. 마지막 줄에 "자세한 내용은 원본 영상을 확인하세요"와 출처(채널명)를 표기하세요.
3. 해시태그는 10~15개, AI 관련 대중적 태그와 세부 주제 태그를 섞어 구성하세요.
4. 과장되거나 자극적인 표현, 이모지는 사용하지 마세요.

[출력 형식]
반드시 아래 JSON 형식으로만 응답하세요. 다른 설명은 붙이지 마세요.
{{
  "caption": "캡션 본문 전체",
  "hashtags": ["#태그1", "#태그2", "..."]
}}
"""

    응답 = 한국어_완성(system_prompt, user_prompt, max_tokens=700, max_tokens_fallback=500)
    if 응답 is None:
        return None

    try:
        json_시작 = 응답.index("{")
        json_끝 = 응답.rindex("}") + 1
        결과 = json.loads(응답[json_시작:json_끝])
    except (ValueError, json.JSONDecodeError) as e:
        print(f"  [경고] 캡션/해시태그 JSON 파싱 실패: {e}\n원본 응답: {응답}")
        return None

    결과["hashtag_text"] = " ".join(결과.get("hashtags", []))
    return 결과


if __name__ == "__main__":
    샘플요약 = {
        "summary": "오픈AI가 더 빠르고 사실적인 이미지 생성 모델을 공개했습니다.",
        "points": ["생성 속도가 기존 대비 3배 빨라짐", "사실적인 인물 표현 개선"],
    }
    결과 = 캡션_해시태그_생성(샘플요약, "테크채널", "https://youtube.com/watch?v=abc")
    print(json.dumps(결과, ensure_ascii=False, indent=2))
