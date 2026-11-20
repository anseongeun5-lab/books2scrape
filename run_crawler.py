"""crawling_prompt.md 명세에 맞춰 구현된 실전 자동화 웹 크롤러 스크립트입니다.

주요 구현 사양:
1. 웹 트래픽 방지를 위한 크롤링 대기 시간 (도서별 0.1초)
2. 웹 페이지 변경 후 1초 대기 후 크롤링 진행 (안정적 렌더링 보장)
3. 에러 발생 시 최대 3회 재시도(Retry) 메커니즘 적용 후 실패 시 안전 종료
4. uv 가상 환경(.venv)에서 즉시 실행 가능 (uv run python run_crawler.py)
"""

import asyncio
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import openpyxl  # 엑셀 파일 저장을 위한 오픈소스 라이브러리
import requests  # 이미지 바이너리 다운로드를 위한 HTTP 라이브러리
from playwright.async_api import Page, async_playwright

# 영문 별점 텍스트를 숫자(1~5)로 매핑하는 변환 사전
RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

# 요구사항: 에러 발생 시 최대 3번 재시도
MAX_RETRIES = 3


def sanitize_filename(name: str) -> str:
    """운영체제에서 지원하지 않는 특수문자를 제거하여 안전한 파일명을 생성합니다."""
    # 윈도우/맥 파일명 금지 특수문자 제거
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    # 연속된 공백을 단일 밑줄(_)로 치환 후 여백 정리
    return re.sub(r"\s+", "_", cleaned).strip()


async def navigate_page_with_retry(page: Page, url: str) -> bool:
    """웹 페이지 이동 시 에러가 발생할 경우 최대 3회 재시도하며, 변경 후 1초 대기합니다."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[*] 웹페이지 이동 시도 ({attempt}/{MAX_RETRIES}회): {url}")
            # 웹페이지 이동 수행 (DOM이 준비될 때까지 대기)
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)

            # [요구사항 2] 웹 페이지 변경 후 1초 후 크롤링 진행
            print(
                "[*] 웹 페이지 로드 완료: 안정적인 데이터 로딩을 위해 1초간 대기합니다..."
            )
            await asyncio.sleep(1.0)
            return True
        except Exception as e:
            print(f"[!] 페이지 이동 중 에러 발생 ({attempt}/{MAX_RETRIES}회): {e}")
            if attempt < MAX_RETRIES:
                # 재시도 전 1초 대기
                await asyncio.sleep(1.0)
            else:
                # [요구사항 3] 3번 재시도 후에도 안 되면 에러 출력 후 실패 반환
                print(
                    "[치명적 오류] 3회 재시도를 모두 실패하여 페이지 이동을 중단합니다."
                )
                return False
    return False


def download_image_with_retry(
    session: requests.Session, image_url: str, save_path: Path
) -> bool:
    """도서 표지 이미지 다운로드 중 에러 발생 시 최대 3회 재시도합니다."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 이미지 바이너리 다운로드 요청
            response = session.get(image_url, timeout=10)
            if response.status_code == 200:
                # 바이너리 파일로 디스크에 쓰기
                with open(save_path, "wb") as f_img:
                    f_img.write(response.content)
                return True
        except Exception as err:
            if attempt < MAX_RETRIES:
                # 재시도 전 0.5초 대기
                time.sleep(0.5)
            else:
                print(f"[경고] 이미지 다운로드 3회 실패 ({save_path.name}): {err}")
    return False


async def run_crawler_workflow(max_pages: int = 2) -> None:
    """Next 버튼을 누르며 도서 정보를 수집하고 엑셀 및 이미지 파일로 분리 저장하는 메인 워크플로우입니다."""
    # 1. 요구사항에 따른 결과 저장 폴더 설정
    result_dir = Path("scraping_result")
    image_dir = Path("books_cover_image")

    # 폴더가 존재하지 않을 경우 자동 생성
    result_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)

    collected_books = []  # 수집 데이터를 담을 리스트
    book_counter = 1  # 도서 순번

    # 이미지 다운로드용 세션 초기화
    img_session = requests.Session()
    img_session.headers.update(
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )

    # Playwright 비동기 브라우저 시작
    async with async_playwright() as p:
        # 헤드리스 모드로 크롬 브라우저 기동
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        start_url = "https://books.toscrape.com/"

        # 1페이지 이동 (3회 재시도 및 페이지 로드 후 1초 대기)
        nav_success = await navigate_page_with_retry(page, start_url)
        if not nav_success:
            # [요구사항 3] 3번 재시도 후에도 안 되면 종료
            print("[종료] 첫 페이지 접속 불가로 프로그램을 안전하게 종료합니다.")
            await browser.close()
            sys.exit(1)

        current_page = 1
        while current_page <= max_pages:
            print("\n==================================================")
            print(f"📖 {current_page}페이지 도서 크롤링 시작 (URL: {page.url})")
            print("==================================================")

            # 도서 카드 요소 대기
            await page.wait_for_selector("article.product_pod")
            cards = await page.query_selector_all("article.product_pod")
            print(f"[*] 총 {len(cards)}권의 도서 카드 감지")

            for card in cards:
                # (1) 도서 제목 추출 (말줄임표 없는 전체 제목)
                title_elem = await card.query_selector("h3 a")
                title = (
                    await title_elem.get_attribute("title")
                    if title_elem
                    else "제목 없음"
                )

                # (2) 가격 추출 (화폐 기호 제거 및 float 변환)
                price_elem = await card.query_selector("p.price_color")
                price_text = await price_elem.inner_text() if price_elem else "£0.0"
                price_match = re.search(r"([0-9.]+)", price_text)
                price = float(price_match.group(1)) if price_match else 0.0

                # (3) 재고 상태 추출
                stock_elem = await card.query_selector("p.instock.availability")
                availability = (
                    (await stock_elem.inner_text()).strip()
                    if stock_elem
                    else "알 수 없음"
                )

                # (4) 별점 평점 추출 및 숫자로 변환 (1~5 정수)
                rating_elem = await card.query_selector("p.star-rating")
                rating_class = (
                    await rating_elem.get_attribute("class") if rating_elem else ""
                )
                rating = 0
                for eng_num, score in RATING_MAP.items():
                    if eng_num in rating_class:
                        rating = score
                        break

                # (5) 상세 페이지 링크 (완전한 절대 URL 변환)
                rel_detail_url = (
                    await title_elem.get_attribute("href") if title_elem else ""
                )
                detail_url = urljoin(page.url, rel_detail_url)

                # (6) 표지 이미지 링크 및 다운로드 (3회 재시도 적용)
                img_elem = await card.query_selector("div.image_container img")
                rel_img_url = await img_elem.get_attribute("src") if img_elem else ""
                image_url = urljoin(page.url, rel_img_url)

                # 파일명 안전하게 지정 (순번_도서제목.jpg)
                safe_title = sanitize_filename(title)[:35]
                image_filename = f"{book_counter:03d}_{safe_title}.jpg"
                image_path = image_dir / image_filename

                # 이미지 다운로드 수행 (최대 3회 재시도)
                download_image_with_retry(img_session, image_url, image_path)

                # 수집 데이터 추가
                collected_books.append(
                    {
                        "순번": book_counter,
                        "도서제목": title,
                        "가격(£)": price,
                        "재고상태": availability,
                        "별점(숫자)": rating,
                        "상세페이지링크": detail_url,
                        "이미지URL": image_url,
                        "저장된이미지경로": str(image_path),
                    }
                )
                book_counter += 1

                # [요구사항 1] 웹 트래픽 방지를 위한 크롤링 대기 시간 (도서별 0.1초 대기)
                await asyncio.sleep(0.1)

            # [요구사항] Next 버튼을 통한 페이지 반복
            next_button = await page.query_selector("li.next a")
            if next_button and current_page < max_pages:
                rel_next_url = await next_button.get_attribute("href")
                next_full_url = urljoin(page.url, rel_next_url)

                print(
                    f"\n[*] Next 버튼 감지: 다음 페이지({current_page + 1}페이지)로 이동합니다..."
                )
                # 다음 페이지 이동 (3회 재시도 및 이동 후 1초 대기 요구사항 적용)
                nav_ok = await navigate_page_with_retry(page, next_full_url)
                if not nav_ok:
                    print(
                        f"[경고] {current_page + 1}페이지 이동 3회 실패로 크롤링을 종료합니다."
                    )
                    break

                current_page += 1
            else:
                if not next_button:
                    print("\n[*] 마지막 페이지(Next 버튼 없음)에 도달했습니다.")
                else:
                    print(
                        f"\n[*] 지정한 최대 수집 페이지({max_pages}페이지)에 도달했습니다."
                    )
                break

        # 브라우저 안전하게 종료
        await browser.close()

    # 3. 엑셀 파일 저장
    excel_path = result_dir / "books_data.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Books_Data"

    if collected_books:
        # 컬럼 헤더 라인 추가
        sheet.append(list(collected_books[0].keys()))
        # 도서 데이터 행 순차 추가
        for item in collected_books:
            sheet.append(list(item.values()))

    # 파일 저장
    workbook.save(excel_path)

    print("\n" + "=" * 60)
    print("🎉 크롤링 및 저장이 성공적으로 완료되었습니다!")
    print(f" - 총 수집 권수: {len(collected_books)}권")
    print(f" - 엑셀 파일 저장 경로: {excel_path.resolve()}")
    print(f" - 표지 이미지 저장 폴더: {image_dir.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    # uv 가상환경에서 실행: uv run python run_crawler.py
    asyncio.run(run_crawler_workflow(max_pages=2))
