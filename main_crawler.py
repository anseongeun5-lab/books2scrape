"""crawling_prompt.md 명세에 맞춰 구현된 실전 자동화 웹 크롤러 스크립트입니다.

[주요 구현 사양]
1. 도서 정보 크롤링 (제목, 가격, 재고상태, 별점 숫자 1~5, 상세페이지 링크, 이미지 링크)
2. 결과는 'scraping_result' 폴더 자동 생성 후 엑셀(.xlsx) 파일로 저장
3. 도서 표지 이미지는 'books_cover_image' 폴더 자동 생성 후 개별 파일(.jpg)로 다운로드
4. 각 페이지의 Next 버튼을 통해 반복 순회 (페이지네이션)
5. 웹 트래픽 방지를 위한 도서별 크롤링 대기 시간
6. 웹 페이지 변경 후 1초 대기 후 크롤링 진행
7. 에러 발생 시 최대 3회 재시도(Retry) 메커니즘 적용 후 실패 시 안전 종료
8. uv 가상 환경(.venv) 완벽 호환
9. CLI 옵션(--pages, --visible 등) 지원으로 사용 편의성 극대화
"""

import argparse
import asyncio
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import openpyxl  # 엑셀 파일 생성을 위한 라이브러리
import requests  # 표지 이미지 파일 다운로드를 위한 HTTP 라이브러리
from playwright.async_api import Page, async_playwright

# 영문 별점 텍스트(One~Five)를 정수 숫자(1~5)로 변환하는 사전
STAR_RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

# 에러 발생 시 최대 재시도 횟수 상수 (요구사항: 3회)
MAX_RETRY_COUNT = 3


def clean_filename(filename: str) -> str:
    """윈도우 및 맥 파일 시스템에서 오류를 유발하는 특수문자를 안전하게 제거합니다."""
    # 파일명 금지 특수문자 제거 (\ / : * ? " < > |)
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    # 연속된 공백 및 언더스코어 정리
    sanitized = re.sub(r"\s+", "_", sanitized).strip()
    # 안전한 파일명 반환 (비어있을 경우 기본값 반환)
    return sanitized if sanitized else "book_cover"


async def fetch_page_with_retry(
    page: Page, target_url: str, wait_seconds: float = 1.0
) -> bool:
    """페이지 이동 시 에러가 발생할 경우 최대 3회 재시도하며, 변경 후 지정 시간 동안 대기합니다."""
    for attempt in range(1, MAX_RETRY_COUNT + 1):
        try:
            print(
                f"[*] 웹페이지 이동 시도 ({attempt}/{MAX_RETRY_COUNT}회): {target_url}"
            )
            # 페이지 이동 수행 (DOM 콘텐츠 로딩 완료 시점까지 대기)
            await page.goto(target_url, wait_until="domcontentloaded", timeout=15000)

            # [요구사항 6] 웹 페이지 변경 후 1초 대기 후 크롤링 진행
            print(
                f"[*] 페이지 변경 감지: 안정적인 렌더링을 위해 {wait_seconds}초간 대기합니다..."
            )
            await asyncio.sleep(wait_seconds)
            return True
        except Exception as error_msg:
            print(
                f"[!] 페이지 이동 중 에러 발생 ({attempt}/{MAX_RETRY_COUNT}회): {error_msg}"
            )
            if attempt < MAX_RETRY_COUNT:
                # 다음 재시도 전 1초 대기
                await asyncio.sleep(1.0)
            else:
                # [요구사항 7] 3회 재시도 모두 실패 시 에러 출력 후 실패 반환
                print(
                    f"[치명적 오류] 3회 재시도 모두 실패하여 작업을 중단합니다: {target_url}"
                )
                return False
    return False


def download_cover_image_with_retry(
    http_session: requests.Session, image_url: str, save_destination: Path
) -> bool:
    """표지 이미지 다운로드 중 에러 발생 시 최대 3회 재시도합니다."""
    # 이미 다운로드된 파일이 있다면 중복 다운로드 건너뜀
    if save_destination.exists():
        return True

    for attempt in range(1, MAX_RETRY_COUNT + 1):
        try:
            # 이미지 바이너리 데이터 요청 (10초 타임아웃)
            resp = http_session.get(image_url, timeout=10)
            if resp.status_code == 200:
                # 디스크에 바이너리 파일로 쓰기
                with open(save_destination, "wb") as image_file:
                    image_file.write(resp.content)
                return True
        except Exception as err:
            if attempt < MAX_RETRY_COUNT:
                # 재시도 전 0.5초 대기
                time.sleep(0.5)
            else:
                print(
                    f"[경고] 이미지 다운로드 3회 실패 ({save_destination.name}): {err}"
                )
    return False


async def start_crawling(
    max_pages: int = 2,
    headless: bool = True,
    page_wait_delay: float = 1.0,
) -> None:
    """Next 버튼을 누르며 도서 정보를 수집하고 엑셀 및 이미지 파일로 분리 저장하는 메인 크롤러입니다."""
    # [요구사항 2, 3] 저장 대상 폴더 경로 설정 (없으면 자동 생성)
    result_folder = Path("scraping_result")
    image_folder = Path("books_cover_image")

    # 디렉터리가 없을 경우 자동으로 생성 (parents=True, exist_ok=True)
    result_folder.mkdir(parents=True, exist_ok=True)
    image_folder.mkdir(parents=True, exist_ok=True)

    collected_data = []  # 수집된 도서 딕셔너리들을 보관할 리스트
    book_index = 1  # 1번부터 매겨질 도서 순번

    # 표지 이미지 다운로드를 위한 HTTP 세션 객체 초기화
    http_session = requests.Session()
    http_session.headers.update(
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )

    # Playwright 비동기 실행 환경 진입
    async with async_playwright() as playwright:
        # headless 옵션에 따라 브라우저 창 표시 여부 결정
        browser = await playwright.chromium.launch(
            headless=headless,
            slow_mo=100 if not headless else 0,
        )
        # 새 브라우저 탭(페이지) 열기
        page = await browser.new_page()

        # 시작 주소 설정
        start_url = "https://books.toscrape.com/"

        # 첫 페이지 이동 (3회 재시도 및 이동 후 1초 대기 적용)
        page_load_success = await fetch_page_with_retry(
            page, start_url, wait_seconds=page_wait_delay
        )
        if not page_load_success:
            # 3회 실패 시 프로그램 안전하게 종료
            print("[종료] 시작 페이지 접속에 실패하여 프로그램을 종료합니다.")
            await browser.close()
            sys.exit(1)

        page_number = 1
        while page_number <= max_pages:
            print("\n" + "=" * 55)
            print(f"📖 [{page_number}페이지] 크롤링 시작 (URL: {page.url})")
            print("=" * 55)

            # 도서 카드 요소가 화면에 로딩될 때까지 대기
            await page.wait_for_selector("article.product_pod")
            # 현재 페이지의 모든 도서 카드 검색
            cards = await page.query_selector_all("article.product_pod")
            print(f"[*] {page_number}페이지에서 {len(cards)}권의 도서를 발견했습니다.")

            for card in cards:
                # 1. 도서 제목 추출 (말줄임표 없는 full title)
                title_tag = await card.query_selector("h3 a")
                book_title = (
                    await title_tag.get_attribute("title")
                    if title_tag
                    else "제목 미확인"
                )

                # 2. 판매 가격 추출 (통화 기호 £ 제거 후 float 변환)
                price_tag = await card.query_selector("p.price_color")
                price_text = await price_tag.inner_text() if price_tag else "£0.0"
                price_match = re.search(r"([0-9.]+)", price_text)
                price_value = float(price_match.group(1)) if price_match else 0.0

                # 3. 재고 상태 추출
                stock_tag = await card.query_selector("p.instock.availability")
                stock_status = (
                    (await stock_tag.inner_text()).strip()
                    if stock_tag
                    else "재고 미확인"
                )

                # 4. 별점 평점 추출 (영문 클래스를 숫자 1~5로 필수 변환)
                rating_tag = await card.query_selector("p.star-rating")
                rating_classes = (
                    await rating_tag.get_attribute("class") if rating_tag else ""
                )
                rating_number = 0
                for eng_key, num_val in STAR_RATING_MAP.items():
                    if eng_key in rating_classes:
                        # 영문과 일치하는 숫자 할당
                        rating_number = num_val
                        break

                # 5. 상세 페이지 링크 (완전한 절대 URL 변환)
                rel_detail_link = (
                    await title_tag.get_attribute("href") if title_tag else ""
                )
                absolute_detail_url = urljoin(page.url, rel_detail_link)

                # 6. 표지 이미지 링크 추출 및 파일 다운로드
                img_tag = await card.query_selector("div.image_container img")
                rel_img_src = (
                    (await img_tag.get_attribute("src") if img_elem else "")
                    if (img_elem := img_tag)
                    else ""
                )
                absolute_img_url = urljoin(page.url, rel_img_src)

                # 특수문자 제거된 안전한 이미지 파일명 생성 (예: 001_A_Light_in_the_Attic.jpg)
                safe_title_prefix = clean_filename(book_title)[:35]
                image_file_name = f"{book_index:03d}_{safe_title_prefix}.jpg"
                image_save_path = image_folder / image_file_name

                # [요구사항 3] 표지 이미지 파일 다운로드 (3회 재시도 적용)
                download_cover_image_with_retry(
                    http_session, absolute_img_url, image_save_path
                )

                # [요구사항 1] 수집 항목 딕셔너리 구성
                collected_data.append(
                    {
                        "순번": book_index,
                        "도서제목": book_title,
                        "가격(£)": price_value,
                        "재고상태": stock_status,
                        "별점(숫자)": rating_number,
                        "상세페이지링크": absolute_detail_url,
                        "이미지URL": absolute_img_url,
                        "저장된이미지경로": str(image_save_path),
                    }
                )
                book_index += 1

                # [요구사항 5] 웹 트래픽 방지를 위한 도서별 크롤링 대기 시간 (0.1초)
                await asyncio.sleep(0.1)

            # [요구사항 4] 각 페이지의 Next 버튼을 통해 반복
            next_btn = await page.query_selector("li.next a")
            if next_btn and page_number < max_pages:
                rel_next_href = await next_btn.get_attribute("href")
                next_page_url = urljoin(page.url, rel_next_href)

                print(
                    f"\n[*] Next 버튼 감지: 다음 페이지({page_number + 1}페이지)로 이동합니다..."
                )
                # 다음 페이지 이동 (최대 3회 재시도 및 이동 후 1초 대기)
                nav_ok = await fetch_page_with_retry(
                    page, next_page_url, wait_seconds=page_wait_delay
                )
                if not nav_ok:
                    print(
                        f"[경고] {page_number + 1}페이지 이동 실패로 크롤링을 종료합니다."
                    )
                    break

                page_number += 1
            else:
                if not next_btn:
                    print("\n[*] 마지막 페이지(Next 버튼 없음)에 도달했습니다.")
                else:
                    print(
                        f"\n[*] 지정된 최대 수집 페이지({max_pages}페이지)에 도달했습니다."
                    )
                break

        # 브라우저 안전하게 종료
        await browser.close()

    # [요구사항 2] 크롤링한 정보를 엑셀 파일(.xlsx)에 저장
    excel_file_path = result_folder / "books_data.xlsx"
    workbook = openpyxl.Workbook()
    active_sheet = workbook.active
    active_sheet.title = "Books_Data"

    if collected_data:
        # 첫 번째 행에 한글 컬럼 헤더 작성
        active_sheet.append(list(collected_data[0].keys()))
        # 도서 데이터 행 순차 추가
        for item in collected_data:
            active_sheet.append(list(item.values()))

    # 엑셀 파일 저장 완료
    workbook.save(excel_file_path)

    # 최종 결과 보고 출력
    print("\n" + "=" * 60)
    print("🎉 웹 크롤링 및 파일 저장이 성공적으로 완료되었습니다!")
    print(f" • 총 수집 도서 권수: {len(collected_data)}권")
    print(f" • 엑셀 파일 저장 위치: {excel_file_path.resolve()}")
    print(f" • 표지 이미지 저장 폴더: {image_folder.resolve()}")
    print("=" * 60)


def parse_arguments() -> argparse.Namespace:
    """사용자가 터미널에서 지정할 수 있는 명령줄 옵션들을 정의합니다."""
    parser = argparse.ArgumentParser(
        description="Books to Scrape 사이트 자동화 웹 크롤러 (Playwright)"
    )
    # 최대 수집 페이지 수 옵션 (--pages, -p)
    parser.add_argument(
        "--pages",
        "-p",
        type=int,
        default=2,
        help="스크래핑할 최대 페이지 수 (기본값: 2)",
    )
    # 브라우저 창 시각화 옵션 (--visible, -v)
    parser.add_argument(
        "--visible",
        "-v",
        action="store_true",
        help="헤드리스 모드를 끄고 브라우저 창을 실제로 띄워서 동작 확인",
    )
    # 페이지 이동 후 대기 시간 옵션 (--delay, -d)
    parser.add_argument(
        "--delay",
        "-d",
        type=float,
        default=1.0,
        help="페이지 변경 후 대기 시간(초) (기본값: 1.0)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    # 터미널 인자 파싱
    cli_args = parse_arguments()

    # 비동기 크롤러 실행
    asyncio.run(
        start_crawling(
            max_pages=cli_args.pages,
            headless=not cli_args.visible,
            page_wait_delay=cli_args.delay,
        )
    )
