# =============================================
# notion_client.py — STEP5: 노션 "카드뉴스 발행 관리" DB 연동
# 클로바노트 자동화(12. 클로바노트 자동화\app.py)의 REST API 직접 호출 패턴 재사용
# GitHub Actions 헤드리스 환경에서는 Notion MCP 커넥터를 쓸 수 없으므로
# Internal Integration 토큰으로 REST API를 직접 호출한다.
# =============================================

from datetime import datetime, timezone, timedelta

import requests

from config import NOTION_TOKEN, NOTION_DB_ID

KST = timezone(timedelta(hours=9))
_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def 페이지_생성(제목, 원본영상_url, 요약, 캡션, 해시태그, 이미지_url_목록, 채널명=""):
    """카드뉴스 발행 관리 DB에 새 페이지를 생성하고 (page_id, page_url)을 반환합니다."""
    properties = {
        "제목": {"title": [{"text": {"content": 제목}}]},
        "원본영상": {"url": 원본영상_url},
        "요약": {"rich_text": [{"text": {"content": 요약[:2000]}}]},
        "상태": {"select": {"name": "대기"}},
        "생성일시": {"date": {"start": datetime.now(KST).isoformat()}},
        "카드뉴스이미지": {
            "files": [
                {"type": "external", "name": f"slide_{i+1}.png", "external": {"url": url}}
                for i, url in enumerate(이미지_url_목록)
            ]
        },
    }
    if 채널명:
        properties["채널명"] = {"rich_text": [{"text": {"content": 채널명[:2000]}}]}
    if 캡션:
        properties["캡션"] = {"rich_text": [{"text": {"content": 캡션[:2000]}}]}
    if 해시태그:
        properties["해시태그"] = {"rich_text": [{"text": {"content": 해시태그[:2000]}}]}

    응답 = requests.post(
        "https://api.notion.com/v1/pages",
        headers=_HEADERS,
        json={"parent": {"database_id": NOTION_DB_ID}, "properties": properties},
        timeout=20,
    )

    if 응답.status_code not in (200, 201):
        raise RuntimeError(f"노션 페이지 생성 실패: {응답.status_code} {응답.text}")

    데이터 = 응답.json()
    return 데이터["id"], 데이터["url"]


def 승인된_페이지_목록():
    """상태="승인"인 페이지들을 조회합니다."""
    응답 = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_DB_ID}/query",
        headers=_HEADERS,
        json={"filter": {"property": "상태", "select": {"equals": "승인"}}},
        timeout=20,
    )
    if 응답.status_code != 200:
        raise RuntimeError(f"노션 DB 조회 실패: {응답.status_code} {응답.text}")

    결과 = []
    for 페이지 in 응답.json().get("results", []):
        properties = 페이지["properties"]
        결과.append({
            "page_id": 페이지["id"],
            "page_url": 페이지["url"],
            "title": _제목_추출(properties),
            "source_url": properties.get("원본영상", {}).get("url", ""),
            "summary": _리치텍스트_추출(properties.get("요약")),
            "channel": _리치텍스트_추출(properties.get("채널명")),
        })
    return 결과


def 페이지_업데이트(page_id, 상태=None, 캡션=None, 해시태그=None):
    """페이지 상태/캡션/해시태그를 업데이트합니다."""
    properties = {}
    if 상태:
        properties["상태"] = {"select": {"name": 상태}}
    if 캡션 is not None:
        properties["캡션"] = {"rich_text": [{"text": {"content": 캡션[:2000]}}]}
    if 해시태그 is not None:
        properties["해시태그"] = {"rich_text": [{"text": {"content": 해시태그[:2000]}}]}

    if not properties:
        return

    응답 = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=_HEADERS,
        json={"properties": properties},
        timeout=20,
    )
    if 응답.status_code != 200:
        raise RuntimeError(f"노션 페이지 업데이트 실패: {응답.status_code} {응답.text}")


def _제목_추출(properties):
    title_속성 = properties.get("제목", {}).get("title", [])
    return "".join(t.get("plain_text", "") for t in title_속성)


def _리치텍스트_추출(속성):
    if not 속성:
        return ""
    return "".join(t.get("plain_text", "") for t in 속성.get("rich_text", []))


if __name__ == "__main__":
    page_id, page_url = 페이지_생성(
        "[테스트] 오픈AI 신모델 발표",
        "https://youtube.com/watch?v=abc",
        "오픈AI가 새로운 이미지 생성 모델을 발표했습니다.",
        "", "",
        ["https://raw.githubusercontent.com/example/repo/main/output/test/slide_1.png"],
    )
    print(f"생성됨: {page_url}")
