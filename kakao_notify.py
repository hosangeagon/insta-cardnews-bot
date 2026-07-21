# =============================================
# kakao_notify.py — STEP6: 카카오 "나에게 보내기" 알림
# news_bot.py의 검증된 토큰 갱신/전송 패턴 재사용
# =============================================

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

from config import KAKAO_REST_API_KEY, KAKAO_CLIENT_SECRET

_BASE_DIR = Path(__file__).parent
KAKAO_TOKEN_FILE = _BASE_DIR / "kakao_token.json"
KST = timezone(timedelta(hours=9))


def 카카오_토큰_갱신():
    with open(KAKAO_TOKEN_FILE, "r", encoding="utf-8") as f:
        토큰정보 = json.load(f)

    데이터 = {
        "grant_type": "refresh_token",
        "client_id": KAKAO_REST_API_KEY,
        "refresh_token": 토큰정보["refresh_token"],
    }
    if KAKAO_CLIENT_SECRET:
        데이터["client_secret"] = KAKAO_CLIENT_SECRET

    응답 = requests.post("https://kauth.kakao.com/oauth/token", data=데이터)
    새토큰 = 응답.json()

    if "access_token" not in 새토큰:
        raise RuntimeError(f"카카오 토큰 갱신 실패: {새토큰}")

    토큰정보["access_token"] = 새토큰["access_token"]
    if "refresh_token" in 새토큰:
        토큰정보["refresh_token"] = 새토큰["refresh_token"]
        토큰정보["refresh_token_updated_at"] = datetime.now().isoformat()

    with open(KAKAO_TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(토큰정보, f, ensure_ascii=False, indent=2)

    return 토큰정보["access_token"]


def _메시지_전송(액세스토큰, 텍스트, 링크, 버튼제목):
    template = {
        "object_type": "text",
        "text": 텍스트,
        "link": {"web_url": 링크, "mobile_web_url": 링크},
        "button_title": 버튼제목,
    }
    return requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={
            "Authorization": f"Bearer {액세스토큰}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"template_object": json.dumps(template, ensure_ascii=False)},
    )


def 승인_요청_알림(카드뉴스_제목, notion_url):
    """STEP6: 새 카드뉴스가 생성되어 승인 대기 중임을 알립니다."""
    요일목록 = ["월", "화", "수", "목", "금", "토", "일"]
    지금 = datetime.now(KST)
    오늘 = 지금.strftime(f"%Y년 %m월 %d일 ({요일목록[지금.weekday()]})")

    텍스트 = (
        f"[카드뉴스 발행 대기]\n{오늘}\n\n"
        f"'{카드뉴스_제목}' 카드뉴스가 준비됐습니다.\n"
        f"확인 후 노션에서 승인해 주세요."
    )

    액세스토큰 = 카카오_토큰_갱신()
    응답 = _메시지_전송(액세스토큰, 텍스트, notion_url, "카드뉴스 확인하기")
    if 응답.status_code == 200:
        print(f"[{지금.strftime('%H:%M')}] 승인 요청 알림 전송 완료: {카드뉴스_제목}")
    else:
        print(f"승인 요청 알림 전송 오류: {응답.text}")
    return 응답.status_code == 200


def 업로드_준비_알림(카드뉴스_제목, notion_url):
    """check_approval.py: 승인된 카드뉴스의 캡션/해시태그까지 준비 완료됨을 알립니다."""
    지금 = datetime.now(KST)

    텍스트 = (
        f"[업로드 준비 완료]\n{지금.strftime('%H:%M')}\n\n"
        f"'{카드뉴스_제목}' 이미지·캡션이 모두 준비됐습니다.\n"
        f"노션에서 확인 후 인스타그램 앱에서 직접 업로드해 주세요."
    )

    액세스토큰 = 카카오_토큰_갱신()
    응답 = _메시지_전송(액세스토큰, 텍스트, notion_url, "노션에서 확인하기")
    if 응답.status_code == 200:
        print(f"[{지금.strftime('%H:%M')}] 업로드 준비 알림 전송 완료: {카드뉴스_제목}")
    else:
        print(f"업로드 준비 알림 전송 오류: {응답.text}")
    return 응답.status_code == 200


if __name__ == "__main__":
    승인_요청_알림("[테스트] 오픈AI 신모델 발표", "https://notion.so/example")
