# =============================================
# generate_daily.py — STEP1~6 오케스트레이션
# 매일 1회 실행: 유튜브 3건 탐색 → 자막정리 → 요약 → 카드뉴스 렌더링
#                → 이미지 깃허브 push → 노션 페이지 생성 → 카카오 알림
# =============================================

import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from config import GITHUB_RAW_BASE
from youtube_search import 오늘의_영상_3건
from transcript import 자막_정리
from summarize import 카드뉴스_요약
from render_cardnews import 카드뉴스_렌더링
from notion_client import 페이지_생성
from kakao_notify import 승인_요청_알림

KST = timezone(timedelta(hours=9))
OUTPUT_ROOT = Path(__file__).parent / "output"


def _git_커밋_푸시(메시지):
    """렌더링된 이미지를 저장소에 커밋·푸시합니다 (raw.githubusercontent 호스팅용).
    로컬에 원격 저장소가 아직 없으면 실패해도 파이프라인은 계속 진행합니다."""
    try:
        subprocess.run(["git", "add", "output"], cwd=Path(__file__).parent, check=True)
        결과 = subprocess.run(
            ["git", "commit", "-m", 메시지],
            cwd=Path(__file__).parent, capture_output=True, text=True, encoding="utf-8",
        )
        if 결과.returncode != 0:
            print(f"  [git commit 생략] {결과.stdout.strip() or 결과.stderr.strip()}")
            return
        subprocess.run(["git", "push"], cwd=Path(__file__).parent, check=True)
        print("  이미지 커밋·푸시 완료")
    except Exception as e:
        print(f"  [경고] git 커밋/푸시 실패 — GitHub 저장소 설정 전이면 정상입니다: {e}")


def _이미지_URL_목록(폴더명, 개수=5):
    if not GITHUB_RAW_BASE:
        print("  [경고] GITHUB_RAW_BASE 미설정 — 노션에 이미지 URL 없이 저장합니다.")
        return []
    return [f"{GITHUB_RAW_BASE}/output/{폴더명}/slide_{i}.png" for i in range(1, 개수 + 1)]


def 영상_1건_처리(영상, 순번, 날짜문자열):
    제목, 채널, url, video_id = 영상["title"], 영상["channel"], 영상["url"], 영상["video_id"]
    print(f"\n[{순번}] {제목} ({채널}) 처리 시작")

    print("  STEP2: 자막 추출/정리 중...")
    자막결과 = 자막_정리(video_id, 제목, 채널)
    if not 자막결과["ok"]:
        print(f"  [건너뜀] {자막결과['reason']}")
        return False

    print("  STEP3: 카드뉴스 요약 생성 중...")
    요약 = 카드뉴스_요약(자막결과["script"], 제목, 채널, url)
    if 요약 is None:
        print("  [건너뜀] 요약 생성 실패")
        return False

    print("  STEP4: 카드뉴스 이미지 렌더링 중...")
    폴더명 = f"{날짜문자열}_{순번}"
    카드뉴스_렌더링(요약, OUTPUT_ROOT / 폴더명)

    이미지_URL_목록 = _이미지_URL_목록(폴더명)

    print("  STEP5: 노션 페이지 생성 중...")
    _, page_url = 페이지_생성(
        요약["cover_title"], url, 요약["summary"], "", "", 이미지_URL_목록, 채널명=채널,
    )
    print(f"  노션 페이지: {page_url}")

    print("  STEP6: 카카오 승인 요청 알림 전송 중...")
    승인_요청_알림(요약["cover_title"], page_url)

    return True


def 오늘의_카드뉴스_생성():
    print(f"\n[{datetime.now(KST).strftime('%Y-%m-%d %H:%M')}] 카드뉴스 생성 시작")

    print("STEP1: 유튜브 화제 영상 3건 탐색 중...")
    영상목록 = 오늘의_영상_3건()
    if not 영상목록:
        print("[종료] 조건을 만족하는 영상이 없습니다.")
        return

    날짜문자열 = datetime.now(KST).strftime("%Y%m%d")
    처리건수 = 0

    for i, 영상 in enumerate(영상목록, 1):
        try:
            if 영상_1건_처리(영상, i, 날짜문자열):
                처리건수 += 1
        except Exception as e:
            print(f"  [오류] {영상.get('title', '?')} 처리 중 예외 발생: {e}")

        if i < len(영상목록):
            time.sleep(20)  # Groq 요청 한도 여유 확보

    if 처리건수 > 0:
        _git_커밋_푸시(f"카드뉴스 자동 생성 {날짜문자열} ({처리건수}건)")

    print(f"\n[완료] 총 {len(영상목록)}건 중 {처리건수}건 처리 완료")


if __name__ == "__main__":
    오늘의_카드뉴스_생성()
