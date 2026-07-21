# =============================================
# transcript.py — STEP2: 자막 추출 및 정리
#
# [지시사항]
# 1. 타임스탬프/잡음 제거, 문단 단위로 자연스럽게 정리 (원문 의미 왜곡 금지)
# 2. 영어 자막이면 정리와 동시에 한국어로 번역
# 3. 자막 없음/2분 미만이면 요약 불가로 표시하고 다음 단계로 넘어가지 않음
# =============================================

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

from groq_client import 한국어_완성

MIN_DURATION_SECONDS = 120  # 2분


def _원문_자막_가져오기(video_id):
    """자막 원문과 언어, 총 길이(초)를 반환합니다. 실패 시 (None, None, 0)."""
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        try:
            transcript = transcript_list.find_transcript(["ko"])
            언어 = "ko"
        except NoTranscriptFound:
            transcript = transcript_list.find_transcript(["en"])
            언어 = "en"

        구간목록 = transcript.fetch()
        원문 = " ".join(구간.text for 구간 in 구간목록)
        총길이 = 구간목록[-1].start + 구간목록[-1].duration if len(구간목록) else 0

        return 원문, 언어, 총길이

    except (TranscriptsDisabled, NoTranscriptFound):
        return None, None, 0
    except Exception as e:
        print(f"  [자막 추출 오류] {video_id}: {e}")
        return None, None, 0


def 자막_정리(video_id, 영상제목, 채널명):
    """자막을 정리·번역합니다.
    반환값: {"ok": True, "script": ..., "lang": ..., "length": ...} 또는
            {"ok": False, "reason": "..."}
    """
    원문, 언어, 총길이 = _원문_자막_가져오기(video_id)

    if 원문 is None:
        return {"ok": False, "reason": "자막이 없어 요약이 어려운 영상입니다."}

    if 총길이 < MIN_DURATION_SECONDS:
        return {"ok": False, "reason": f"영상 길이가 2분 미만(약 {int(총길이)}초)이라 요약이 어렵습니다."}

    system_prompt = "당신은 유튜브 영상 자막을 정리하는 에디터입니다."
    user_prompt = f"""아래는 유튜브 영상의 원문 자막입니다.

영상 제목: {영상제목}
채널명: {채널명}
원문 언어: {"한국어" if 언어 == "ko" else "영어"}

[지시사항]
1. 타임스탬프나 반복되는 잡음(음, 어 등)이 있으면 제거하세요.
2. 문단 단위로 자연스럽게 정리하되, 원문 의미를 왜곡하지 마세요.
3. 원문이 영어라면 정리와 동시에 한국어로 번역하세요.

[원문 자막]
{원문[:12000]}
"""

    정리된_스크립트 = 한국어_완성(system_prompt, user_prompt, max_tokens=2000, max_tokens_fallback=1500)

    if 정리된_스크립트 is None:
        return {"ok": False, "reason": "자막 정리 중 AI 호출에 실패했습니다."}

    return {
        "ok": True,
        "script": 정리된_스크립트,
        "lang": 언어,
        "length_seconds": int(총길이),
    }


if __name__ == "__main__":
    import sys
    video_id = sys.argv[1] if len(sys.argv) > 1 else "dQw4w9WgXcQ"
    결과 = 자막_정리(video_id, "테스트 영상", "테스트 채널")
    print(결과)
