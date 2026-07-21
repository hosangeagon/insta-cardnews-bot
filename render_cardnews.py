# =============================================
# render_cardnews.py — STEP4: 카드뉴스 이미지 렌더링
# cardnews_template.html의 플레이스홀더를 요약 내용으로 채운 뒤
# Playwright headless 브라우저로 슬라이드별 PNG를 캡처합니다.
# =============================================

import html
from pathlib import Path

from playwright.sync_api import sync_playwright

TEMPLATE_PATH = Path(__file__).parent / "cardnews_template.html"
SLIDE_IDS = ["slide-1", "slide-2", "slide-3", "slide-4", "slide-5"]


def _템플릿_채우기(요약):
    템플릿 = TEMPLATE_PATH.read_text(encoding="utf-8")

    포인트목록 = 요약.get("points", ["", "", "", "", ""])
    while len(포인트목록) < 5:
        포인트목록.append("")

    치환값 = {
        "{{TITLE}}": 요약.get("cover_title", ""),
        "{{HOOK}}": 요약.get("hook", ""),
        "{{SUMMARY}}": 요약.get("summary", ""),
        "{{POINT1}}": 포인트목록[0],
        "{{POINT2}}": 포인트목록[1],
        "{{POINT3}}": 포인트목록[2],
        "{{POINT4}}": 포인트목록[3],
        "{{POINT5}}": 포인트목록[4],
        "{{COMMENT}}": 요약.get("comment", ""),
        "{{SOURCE_CHANNEL}}": 요약.get("source_channel", ""),
        "{{SOURCE_TITLE}}": 요약.get("source_title", ""),
    }

    for 토큰, 값 in 치환값.items():
        템플릿 = 템플릿.replace(토큰, html.escape(str(값)))

    return 템플릿


def 카드뉴스_렌더링(요약, 출력_폴더):
    """요약 내용을 슬라이드에 채운 뒤 5장 PNG로 저장합니다.
    반환값: 생성된 PNG 파일 경로(Path) 리스트
    """
    출력_폴더 = Path(출력_폴더)
    출력_폴더.mkdir(parents=True, exist_ok=True)

    html_내용 = _템플릿_채우기(요약)
    임시_html = 출력_폴더 / "_render.html"
    임시_html.write_text(html_내용, encoding="utf-8")

    생성된_파일 = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        page.goto(f"file://{임시_html.resolve()}")

        for i, slide_id in enumerate(SLIDE_IDS, 1):
            파일경로 = 출력_폴더 / f"slide_{i}.png"
            page.locator(f"#{slide_id}").screenshot(path=str(파일경로))
            생성된_파일.append(파일경로)

        browser.close()

    임시_html.unlink()
    return 생성된_파일


if __name__ == "__main__":
    샘플 = {
        "cover_title": "오픈AI 신모델 발표",
        "hook": "이제 이미지 생성이 훨씬 빨라집니다",
        "summary": "오픈AI가 더 빠르고 사실적인 이미지 생성 모델을 공개했습니다.",
        "points": [
            "생성 속도가 기존 대비 3배 빨라짐",
            "사실적인 인물 표현 개선",
            "저해상도 이미지 업스케일 지원",
            "무료 사용자도 제한적으로 이용 가능",
        ],
        "comment": "실제 품질 개선 여부는 사용자 반응을 더 지켜봐야 합니다.",
        "source_channel": "테크채널",
        "source_title": "오픈AI 신모델 발표",
    }
    파일목록 = 카드뉴스_렌더링(샘플, Path(__file__).parent / "output" / "_test")
    for f in 파일목록:
        print(f)
