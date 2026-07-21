# =============================================
# check_approval.py — 노션 승인 상태 폴링 (10~15분 주기)
#
# [참고: 노션 상태 확인 로직]
# 1. "카드뉴스 발행 관리" DB에서 상태="승인"인 페이지를 조회
# 2. STEP7(캡션·해시태그) 실행 후 노션 페이지에 채워넣음
# 3. 카카오로 "이미지+캡션 준비완료, 인스타 앱에서 업로드해주세요" 알림
# 4. 상태를 "업로드대기(수동)"로 변경 (중복 알림 방지)
#    — 실제 인스타그램 게시는 공식 개인계정용 API가 없어 수동으로 진행합니다.
#      크리에이터 계정으로 전환하면 Graph API로 완전 자동 게시로 확장할 수 있습니다.
# =============================================

from datetime import datetime, timezone, timedelta

from notion_client import 승인된_페이지_목록, 페이지_업데이트
from caption_hashtags import 캡션_해시태그_생성
from kakao_notify import 업로드_준비_알림

KST = timezone(timedelta(hours=9))


def 승인_확인_및_처리():
    print(f"\n[{datetime.now(KST).strftime('%Y-%m-%d %H:%M')}] 승인 상태 확인 중...")

    페이지목록 = 승인된_페이지_목록()
    if not 페이지목록:
        print("  승인된 페이지 없음")
        return

    for 페이지 in 페이지목록:
        print(f"  처리 중: {페이지['title']}")
        try:
            결과 = 캡션_해시태그_생성(
                {"summary": 페이지["summary"], "points": []},
                채널명="", url=페이지["source_url"],
            )
            if 결과 is None:
                print(f"  [건너뜀] {페이지['title']} — 캡션/해시태그 생성 실패, 다음 주기에 재시도")
                continue

            페이지_업데이트(
                페이지["page_id"],
                상태="업로드대기(수동)",
                캡션=결과["caption"],
                해시태그=결과["hashtag_text"],
            )

            업로드_준비_알림(페이지["title"], 페이지["page_url"])
            print(f"  완료: {페이지['title']}")

        except Exception as e:
            print(f"  [오류] {페이지['title']} 처리 중 예외 발생: {e}")


if __name__ == "__main__":
    승인_확인_및_처리()
