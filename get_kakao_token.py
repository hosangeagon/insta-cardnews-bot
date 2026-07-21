# =============================================
# get_kakao_token.py — 카카오 토큰 발급 (최초 1회만 로컬에서 실행)
# 실행 전 카카오 디벨로퍼스 콘솔에서 아래 설정 필요:
#   1. 제품 설정 > 카카오 로그인 > 활성화 ON
#   2. Redirect URI에 http://localhost 추가
#   3. 동의항목에서 "카카오톡 메시지 전송" 활성화
# news_bot 프로젝트와 동일한 카카오 앱(REST API 키)을 재사용해도 됩니다 —
# "나에게 보내기"는 앱 단위가 아니라 로그인한 카카오 계정 단위로 동작합니다.
# =============================================

import requests
import json
import webbrowser
from config import KAKAO_REST_API_KEY, KAKAO_CLIENT_SECRET, KAKAO_REDIRECT_URI


def 카카오_토큰_발급():
    인증_URL = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_REST_API_KEY}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        f"&response_type=code"
    )
    print("=" * 50)
    print("[1단계] 브라우저에서 카카오 로그인 창이 열립니다.")
    print("로그인 후 이동된 주소창의 전체 URL을 복사해주세요.")
    print("(주소가 http://localhost?code=... 로 시작합니다)")
    print("=" * 50)
    webbrowser.open(인증_URL)

    리다이렉트_URL = input("\n주소창의 전체 URL을 붙여넣기 하세요:\n> ").strip()

    if "code=" in 리다이렉트_URL:
        인증코드 = 리다이렉트_URL.split("code=")[1].split("&")[0]
    else:
        인증코드 = 리다이렉트_URL

    토큰_URL = "https://kauth.kakao.com/oauth/token"
    데이터 = {
        "grant_type":   "authorization_code",
        "client_id":    KAKAO_REST_API_KEY,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code":         인증코드,
    }
    if KAKAO_CLIENT_SECRET:
        데이터["client_secret"] = KAKAO_CLIENT_SECRET

    응답 = requests.post(토큰_URL, data=데이터)
    토큰정보 = 응답.json()

    if "access_token" not in 토큰정보:
        print(f"\n오류 발생: {토큰정보}")
        return

    from datetime import datetime
    토큰정보["refresh_token_updated_at"] = datetime.now().isoformat()

    with open("kakao_token.json", "w", encoding="utf-8") as f:
        json.dump(토큰정보, f, ensure_ascii=False, indent=2)

    print("\n토큰 발급 완료! kakao_token.json 파일에 저장됐습니다.")
    print("이 파일의 refresh_token 값을 GitHub Secrets의 KAKAO_REFRESH_TOKEN에 등록하세요.")


if __name__ == "__main__":
    카카오_토큰_발급()
