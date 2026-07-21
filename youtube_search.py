# =============================================
# youtube_search.py — STEP1: 유튜브 AI 관련 화제 영상 탐색
#
# [조건]
# - 카테고리: 인공지능(AI) 관련 뉴스, 신제품 출시, 기술 트렌드, 논쟁적 이슈
# - 조회수: 30만 회 이상 / 게시 기간: 최근 7일 이내
# - 하루 최종 선정 건수: 3건 (원본 프롬프트의 "1건" 출력지시 오류를 3건으로 수정)
# - 제외 대상: 광고성 콘텐츠, 단순 브이로그, 저작권 이슈 재업로드 영상
# =============================================

import json
from datetime import datetime, timedelta, timezone

import requests

from config import YOUTUBE_API_KEY
from groq_client import 한국어_완성

VIEW_COUNT_MIN = 300_000
LOOKBACK_DAYS = 7
FINAL_COUNT = 3

검색어_목록 = [
    "AI 신제품 발표", "인공지능 뉴스", "ChatGPT 업데이트",
    "AI 논란", "생성형 AI", "AI 기술 트렌드",
]

# 제외 키워드 — 광고/브이로그/재업로드 성격이 강한 제목 필터
노이즈_키워드 = [
    "광고", "협찬", "브이로그", "vlog", "일상", "재업로드", "리업로드",
    "reupload", "shorts 모음", "asmr",
]


def _노이즈_영상_여부(제목):
    제목_소문자 = 제목.lower()
    return any(k.lower() in 제목_소문자 for k in 노이즈_키워드)


def _영상_검색(검색어, published_after_iso, max_results=15):
    """search.list로 후보 영상 ID를 모읍니다."""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "q": 검색어,
        "part": "snippet",
        "type": "video",
        "order": "viewCount",
        "publishedAfter": published_after_iso,
        "relevanceLanguage": "ko",
        "maxResults": max_results,
    }
    응답 = requests.get(url, params=params, timeout=20)
    데이터 = 응답.json()
    if "items" not in 데이터:
        print(f"  [YouTube 검색 오류] '{검색어}': {데이터.get('error', 데이터)}")
        return []
    return [항목["id"]["videoId"] for 항목 in 데이터["items"] if "videoId" in 항목["id"]]


def _영상_통계_조회(video_ids):
    """videos.list로 조회수/게시일 등 상세 정보를 가져옵니다."""
    if not video_ids:
        return []
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "key": YOUTUBE_API_KEY,
        "id": ",".join(video_ids),
        "part": "snippet,statistics",
    }
    응답 = requests.get(url, params=params, timeout=20)
    데이터 = 응답.json()
    return 데이터.get("items", [])


def 후보_영상_수집():
    """조건(조회수 30만+, 7일 이내)을 만족하는 후보 영상 목록을 모읍니다."""
    KST = timezone(timedelta(hours=9))
    기준시각 = datetime.now(KST) - timedelta(days=LOOKBACK_DAYS)
    published_after_iso = 기준시각.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    수집된_ID = set()
    후보목록 = []

    for 검색어 in 검색어_목록:
        영상ID목록 = _영상_검색(검색어, published_after_iso)
        신규ID목록 = [vid for vid in 영상ID목록 if vid not in 수집된_ID]
        수집된_ID.update(신규ID목록)

        for 항목 in _영상_통계_조회(신규ID목록):
            제목 = 항목["snippet"]["title"]
            if _노이즈_영상_여부(제목):
                continue

            조회수 = int(항목["statistics"].get("viewCount", 0))
            if 조회수 < VIEW_COUNT_MIN:
                continue

            후보목록.append({
                "video_id": 항목["id"],
                "title": 제목,
                "channel": 항목["snippet"]["channelTitle"],
                "url": f"https://www.youtube.com/watch?v={항목['id']}",
                "published_at": 항목["snippet"]["publishedAt"],
                "view_count": 조회수,
            })

    return 후보목록


def 최종_3건_선정(후보목록):
    """Groq에게 후보 중 화제성 높은 3건을 선정하고 선정 사유를 쓰게 합니다."""
    if not 후보목록:
        return []

    # 조회수 내림차순으로 정리해 후보가 너무 많을 때 상위 20개만 LLM에 전달
    후보목록 = sorted(후보목록, key=lambda x: x["view_count"], reverse=True)[:20]

    후보텍스트 = "\n".join(
        f"{i+1}. 제목: {c['title']} | 채널: {c['channel']} | "
        f"조회수: {c['view_count']:,} | 게시일: {c['published_at']} | URL: {c['url']}"
        for i, c in enumerate(후보목록)
    )

    system_prompt = "당신은 유튜브에서 화제성 높은 AI 관련 영상을 찾아내는 리서처입니다."
    user_prompt = f"""아래는 조회수 30만 이상, 최근 7일 이내 게시된 AI 관련 유튜브 영상 후보 목록입니다.
이 중 화제성이 가장 높은 3건을 최종 선정하세요.

[제외 기준]
- 광고성 콘텐츠, 단순 브이로그, 저작권 이슈가 있는 재업로드 영상

[후보 목록]
{후보텍스트}

[출력 형식]
반드시 아래 JSON 배열 형식으로만 응답하세요. 다른 설명은 붙이지 마세요.
[
  {{"index": 1, "reason": "선정 사유 1~2문장"}},
  {{"index": 2, "reason": "선정 사유 1~2문장"}},
  {{"index": 3, "reason": "선정 사유 1~2문장"}}
]
"""

    응답 = 한국어_완성(system_prompt, user_prompt, max_tokens=800, max_tokens_fallback=600)
    if 응답 is None:
        print("  [경고] Groq 선정 실패 — 조회수 상위 3건으로 대체")
        선정 = 후보목록[:FINAL_COUNT]
        for c in 선정:
            c["reason"] = "조회수 기준 상위 영상으로 자동 선정 (AI 선정 실패 대체)"
        return 선정

    try:
        json_시작 = 응답.index("[")
        json_끝 = 응답.rindex("]") + 1
        선정목록 = json.loads(응답[json_시작:json_끝])
    except (ValueError, json.JSONDecodeError) as e:
        print(f"  [경고] Groq 응답 파싱 실패({e}) — 조회수 상위 3건으로 대체")
        선정 = 후보목록[:FINAL_COUNT]
        for c in 선정:
            c["reason"] = "조회수 기준 상위 영상으로 자동 선정 (AI 응답 파싱 실패 대체)"
        return 선정

    결과 = []
    for 항목 in 선정목록[:FINAL_COUNT]:
        idx = 항목.get("index", 0) - 1
        if 0 <= idx < len(후보목록):
            영상 = dict(후보목록[idx])
            영상["reason"] = 항목.get("reason", "")
            결과.append(영상)

    return 결과


def 오늘의_영상_3건():
    후보목록 = 후보_영상_수집()
    print(f"  후보 영상 {len(후보목록)}건 수집 완료")
    선정 = 최종_3건_선정(후보목록)
    print(f"  최종 {len(선정)}건 선정 완료")
    return 선정


if __name__ == "__main__":
    for i, 영상 in enumerate(오늘의_영상_3건(), 1):
        print(f"\n[{i}] {영상['title']} ({영상['channel']})")
        print(f"    조회수: {영상['view_count']:,} | 게시일: {영상['published_at']}")
        print(f"    URL: {영상['url']}")
        print(f"    선정 사유: {영상['reason']}")
