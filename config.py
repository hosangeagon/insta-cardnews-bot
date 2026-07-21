# =============================================
# config.py — API 키 설정 파일
# 실제 키는 .env 파일에 저장됩니다 (커밋되지 않음)
# =============================================

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# YouTube Data API v3 키 (Google Cloud Console, 무료)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Groq API 키 (console.groq.com, 무료, LLM 요약/문구 생성용)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# 카카오 REST API 키 + 클라이언트 시크릿 + 로그인 Redirect URI ("나에게 보내기" 알림용)
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")  # 클라이언트 시크릿 비활성화 시 비워두면 됨
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "http://localhost")

# 노션 Internal Integration 토큰 + "카드뉴스 발행 관리" DB ID
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID", "a716cf87-680b-40a2-a5b8-cc9792773f4c")

# GitHub raw 이미지 URL 베이스 (Notion 파일 속성에 넣을 공개 URL 만들 때 사용)
# 예: https://raw.githubusercontent.com/<user>/<repo>/main
GITHUB_RAW_BASE = os.getenv("GITHUB_RAW_BASE")
