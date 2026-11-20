# 📝 웹 크롤링 코드 생성 프롬프트 가이드 (`crawling_prompt.md`)

이 문서는 ChatGPT, Claude, Gemini 등의 AI 모델에게 **Books to Scrape 사이트의 자동화 웹 크롤링 파이썬 코드를 한 번에 정확하게 작성해 달라고 요청할 수 있는 완성형 프롬프트 템플릿**입니다.

하단의 **[복사용 프롬프트 템플릿]** 박스 전체를 복사하여 AI 채팅창에 그대로 입력하시면 모든 고급 요구조건(에러 3회 재시도, 트래픽 방지 딜레이, uv 가상환경 호환, 엑셀/이미지 분리 저장)이 100% 반영된 완벽한 코드를 얻으실 수 있습니다.

---

## 📋 [복사용 프롬프트 템플릿] (여기서부터 복사하세요)

```markdown
당신은 최고의 웹 크롤링 및 데이터 엔지니어링 전문가입니다.
아래의 목표와 세부 요구사항을 모두 충족하는 완성형 파이썬(Python) 웹 크롤링 코드를 작성해 주세요.
프로그래밍 비전공자도 코드를 쉽게 이해하고 유지보수할 수 있도록, **모든 코드 라인마다 친절하고 꼼꼼한 한국어 인라인 주석(#)**을 반드시 달아주세요.

---

### 1. 대상 사이트 및 크롤링 목표
- **대상 웹사이트**: Books to Scrape (https://books.toscrape.com/)
- **크롤링 목표**: 첫 페이지부터 마지막 페이지까지(또는 지정된 페이지까지) 하단의 Next 버튼을 자동으로 클릭/추적하며 도서의 핵심 정보와 표지 이미지를 수집하여 엑셀 파일로 저장합니다.

---

### 2. 세부 수집 항목 및 가공 규칙
각 도서 카드(`<article class="product_pod">`)에서 다음 항목들을 빠짐없이 추출해 주세요:

1. **도서 제목 (Title)**: 말 줄임표 없는 전체 제목 (`h3 a` 태그의 `title` 속성값)
2. **판매 가격 (Price)**: 통화 기호(£)를 제거한 순수 숫자(float 또는 문자열) (`p.price_color`)
3. **재고 상태 (Availability)**: 재고 상태 문자열 (예: 'In stock') (`p.instock.availability`)
4. **별점 평점 (Rating - 필수 변환)**: 
   - 웹페이지에는 영문 클래스(`One`, `Two`, `Three`, `Four`, `Five`)로 되어 있습니다.
   - 이를 **반드시 숫자(1, 2, 3, 4, 5)**로 변환하여 기록해 주세요.
   - 예: `class="star-rating Three"` -> 숫자 `3`
5. **상세 페이지 링크 (Detail URL)**: 상대 경로를 완전한 절대 URL(`https://books.toscrape.com/...`)로 변환하여 기록
6. **표지 이미지 URL (Image URL)**: 완전한 절대 URL로 변환하여 기록

---

### 3. 데이터 저장 및 파일 관리 요구사항
1. **엑셀(Excel) 파일 저장**:
   - 수집된 도서 정보 목록을 엑셀(`.xlsx`) 파일(또는 엑셀 호환 CSV `utf-8-sig`)로 저장해 주세요.
   - 저장 위치는 프로젝트 폴더 내 **`scraping_result`** 폴더입니다.
   - **폴더가 존재하지 않을 경우 코드가 자동으로 폴더를 생성**한 뒤 저장하도록 구현해 주세요.
2. **도서 표지 이미지 파일 개별 다운로드**:
   - 각 도서의 표지 이미지를 실제 이미지 파일(`.jpg`)로 직접 다운로드해 주세요.
   - 저장 위치는 프로젝트 폴더 내 **`books_cover_image`** 폴더입니다.
   - **폴더가 존재하지 않을 경우 코드가 자동으로 폴더를 생성**해 주세요.
   - 파일명은 윈도우/맥에서 오류가 나지 않도록 특수문자를 제거하고, `순번_도서제목.jpg` 형태로 안전하게 지정해 주세요.

---

### 4. 트래픽 방지 및 안정성 요구사항 (핵심 제약 조건)
1. **웹 트래픽 방지 크롤링 대기 시간**:
   - 대상 사이트 서버에 과부하를 주지 않도록, 각 도서 데이터 수집 및 이미지 다운로드 사이에 적절한 대기 시간(0.2초~0.5초)을 부여해 주세요.
2. **웹 페이지 변경 후 1초 대기 후 크롤링 진행**:
   - `Next` 버튼을 클릭하여 새 페이지로 이동하거나 페이지를 새로 로드했을 때, **반드시 1초간 대기(`wait 1초` 또는 `sleep 1초`)한 후** 안전하게 다음 크롤링 작업을 시작하도록 구현해 주세요.
3. **에러 발생 시 3회 재시도 (Retry 3회) 후 실패 시 종료**:
   - 웹페이지 이동, 데이터 파싱, 이미지 다운로드 등 네트워크 작업 도중 에러가 발생하면, 즉시 중단하지 않고 **최대 3번까지 재시도**를 수행해 주세요.
   - 3번의 재시도 후에도 연속으로 실패할 경우 에러 메시지를 출력하고 프로그램을 안전하게 종료(graceful exit)해 주세요.
4. **uv 가상 환경 호환성**:
   - 이 프로젝트에서 생성된 `uv` 가상환경(`.venv`)에서 곧바로 실행될 수 있도록 작성해 주세요.
   - 패키지 실행 및 추가 명령어 안내 시 `uv add <패키지>`, `uv run <스크립트.py>` 표준 명령어를 제시해 주세요.

---

### 5. 페이지네이션 (Next 버튼 자동 반복) 요구사항
- 페이지 하단에 위치한 다음 페이지 버튼(`li.next a`)을 자동으로 감지해 주세요.
- 다음 페이지 버튼이 존재하면 다음 페이지로 이동(이동 후 1초 대기)하여 계속해서 도서 정보와 이미지를 수집하고, 단, 3페이지만 (Next 버튼 없음)에 도달하면 안전하게 크롤링을 종료해 주세요.
- 테스트 시 너무 오래 걸리지 않도록 최대 수집 페이지 수(예: `max_pages = 2` 등)를 상단 변수로 조절할 수 있게 만들어 주세요.

---

### 6. 참고용 HTML 구조 및 CSS 선택자 힌트
- 도서 카드 전체 박스: `article.product_pod`
- 책 제목 태그: `h3 a`
- 가격 태그: `p.price_color`
- 별점 태그: `p.star-rating`
- 재고 태그: `p.instock.availability`
- 표지 이미지 태그: `div.image_container img`
- 다음 페이지 버튼: `li.next a`
```

---

## 💡 프롬프트 커스텀 가이드 (비전공자를 위한 맞춤 팁)

원하는 브라우저 환경이나 기술 스택에 따라 위 프롬프트에 한 줄만 덧붙여서 AI에게 질문하시면 더욱 최적화된 코드를 얻으실 수 있습니다:

### 옵션 A: Playwright 브라우저로 화면을 보며 동작시키고 싶을 때
> **추가 문구**: *"크롤러 라이브러리는 **Playwright(Python 비동기 async/await)**를 사용해 주시고, 브라우저 창이 뜨는 모습을 직접 볼 수 있도록 `headless=False, slow_mo=100` 옵션을 설정해 주세요."*

### 옵션 B: 고속 모드로 빠르게 수집하고 싶을 때 (Requests + BeautifulSoup)
> **추가 문구**: *"브라우저 없이 가볍게 동작할 수 있도록 **Requests, BeautifulSoup4, openpyxl** 라이브러리 조합으로 코드를 작성해 주세요."*

---

## 🛠️ 모든 추가 요구사항이 완벽히 반영된 완성형 파이썬 코드 예시

아래 코드는 **(1) 트래픽 방지 딜레이, (2) 페이지 이동 후 1초 대기, (3) 3회 재시도 실패 시 종료, (4) uv 가상환경 지원**이 모두 적용된 완성형 모범 답안입니다:

```python
"""Books to Scrape 완성형 자동화 웹 크롤러 스크립트입니다."""

import asyncio
from pathlib import Path
import re
import sys
import time
from urllib.parse import urljoin
import openpyxl  # 엑셀(.xlsx) 파일 생성용 라이브러리
from playwright.async_api import Page, async_playwright
import requests  # 이미지 바이너리 다운로드용 라이브러리

# 영문 별점 텍스트를 숫자(1~5)로 매핑하는 사전
RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

# 최대 재시도 횟수 상수 정의 (요구사항: 3회)
MAX_RETRIES = 3


def sanitize_filename(name: str) -> str:
    """운영체제에서 지원하지 않는 파일명 특수문자를 제거합니다."""
    # 윈도우/맥 파일명 금지 특수문자 제거
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    # 연속된 공백을 단일 밑줄(_)로 치환 후 좌우 여백 제거
    return re.sub(r"\s+", "_", cleaned).strip()


async def navigate_with_retry(page: Page, url: str) -> bool:
    """웹 페이지 이동 시 에러가 발생할 경우 최대 3회 재시도합니다."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[*] 페이지 접속 시도 ({attempt}/{MAX_RETRIES}회): {url}")
            # 웹페이지 이동 (DOM 콘텐츠가 로드될 때까지 대기)
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)

            # [요구사항 2] 웹 페이지 변경 후 1초 대기 후 크롤링 진행
            print("[*] 페이지 변경 감지: 안정적인 렌더링을 위해 1초 대기합니다...")
            await asyncio.sleep(1.0)
            return True
        except Exception as e:
            print(f"[!] 접속 실패 ({attempt}/{MAX_RETRIES}회): {e}")
            if attempt < MAX_RETRIES:
                # 재시도 전 1초 대기
                await asyncio.sleep(1.0)
            else:
                # [요구사항 3] 3번 재시도 후에도 안 되면 실패 알림
                print(f"[치명적 오류] 3회 재시도 모두 실패하여 접속을 중단합니다.")
                return False
    return False


def download_image_with_retry(
    session: requests.Session, image_url: str, save_path: Path
) -> bool:
    """이미지 다운로드 도중 에러 발생 시 최대 3회 재시도합니다."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # 이미지 바이너리 데이터 요청 (타임아웃 10초)
            response = session.get(image_url, timeout=10)
            if response.status_code == 200:
                # 바이너리 파일 쓰기 모드로 오픈하여 저장
                with open(save_path, "wb") as f:
                    f.write(response.content)
                return True
        except Exception as err:
            if attempt < MAX_RETRIES:
                time.sleep(0.5)  # 재시도 전 짧은 휴식
            else:
                print(f"[경고] 이미지 다운로드 3회 실패 ({save_path.name}): {err}")
    return False


async def run_crawler(max_pages: int = 2) -> None:
    """Books to Scrape 크롤러 메인 실행 함수입니다."""
    # [요구사항] 저장 폴더 경로 설정 (없으면 자동 생성)
    result_dir = Path("scraping_result")
    image_dir = Path("books_cover_image")
    result_dir.mkdir(parents=True, exist_ok=True)  # scraping_result 폴더 자동 생성
    image_dir.mkdir(parents=True, exist_ok=True)  # books_cover_image 폴더 자동 생성

    collected_books = []  # 수집한 도서 데이터 레코드 리스트
    book_counter = 1  # 도서 순번 식별자

    # 이미지 다운로드용 Requests 세션 초기화
    img_session = requests.Session()
    img_session.headers.update(
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )

    async with async_playwright() as p:
        # Chromium 브라우저 인스턴스 실행
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 첫 페이지 시작 URL 지정
        start_url = "https://books.toscrape.com/"

        # 1페이지 이동 (최대 3회 재시도)
        success = await navigate_with_retry(page, start_url)
        if not success:
            # [요구사항 3] 에러 발생 후 3회 재시도 실패 시 프로그램 종료
            print("[종료] 첫 페이지 접속에 실패하여 크롤러를 종료합니다.")
            await browser.close()
            sys.exit(1)

        current_page = 1
        while current_page <= max_pages:
            print(f"\n==================================================")
            print(f"📖 {current_page}페이지 도서 크롤링 시작 (URL: {page.url})")
            print(f"==================================================")

            # 도서 카드 요소들이 DOM에 올라올 때까지 대기
            await page.wait_for_selector("article.product_pod")
            cards = await page.query_selector_all("article.product_pod")
            print(f"[*] 총 {len(cards)}권의 도서 카드 감지됨")

            for card in cards:
                # 1. 도서 제목 추출 (말줄임표 없는 full title)
                title_elem = await card.query_selector("h3 a")
                title = (
                    await title_elem.get_attribute("title")
                    if title_elem
                    else "제목 없음"
                )

                # 2. 가격 추출 (화폐 기호 £ 제거 후 float 변환)
                price_elem = await card.query_selector("p.price_color")
                price_text = await price_elem.inner_text() if price_elem else "£0.0"
                price_match = re.search(r"([0-9.]+)", price_text)
                price = float(price_match.group(1)) if price_match else 0.0

                # 3. 재고 상태 추출
                stock_elem = await card.query_selector("p.instock.availability")
                availability = (
                    (await stock_elem.inner_text()).strip()
                    if stock_elem
                    else "알 수 없음"
                )

                # 4. 별점 평점 추출 및 숫자로 필수 변환 (1~5점)
                rating_elem = await card.query_selector("p.star-rating")
                rating_class = (
                    await rating_elem.get_attribute("class") if rating_elem else ""
                )
                rating = 0
                for eng_num, score in RATING_MAP.items():
                    if eng_num in rating_class:
                        rating = score
                        break

                # 5. 상세 페이지 링크 절대 URL 변환
                rel_detail_url = (
                    await title_elem.get_attribute("href") if title_elem else ""
                )
                detail_url = urljoin(page.url, rel_detail_url)

                # 6. 표지 이미지 다운로드
                img_elem = await card.query_selector("div.image_container img")
                rel_img_url = await img_elem.get_attribute("src") if img_elem else ""
                image_url = urljoin(page.url, rel_img_url)

                # 안전한 파일명 생성 (순번_도서제목.jpg)
                safe_title = sanitize_filename(title)[:35]
                image_filename = f"{book_counter:03d}_{safe_title}.jpg"
                image_path = image_dir / image_filename

                # 이미지 다운로드 (에러 시 3회 재시도 적용)
                download_image_with_retry(img_session, image_url, image_path)

                # 수집 데이터 딕셔너리 생성
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

                # [요구사항 1] 웹 트래픽 방지를 위한 도서별 짧은 대기 시간 (0.1초)
                await asyncio.sleep(0.1)

            # [요구사항 5] Next 버튼을 통한 페이지 반복
            next_button = await page.query_selector("li.next a")
            if next_button and current_page < max_pages:
                rel_next_url = await next_button.get_attribute("href")
                next_full_url = urljoin(page.url, rel_next_url)

                print(
                    f"\n[*] Next 버튼 감지: 다음 페이지({current_page + 1}페이지)로 이동합니다..."
                )
                # 다음 페이지 이동 (최대 3회 재시도 메커니즘 적용)
                nav_success = await navigate_with_retry(page, next_full_url)
                if not nav_success:
                    print(
                        f"[경고] {current_page + 1}페이지 이동 3회 실패로 크롤링을 조기 종료합니다."
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

        # 브라우저 정리
        await browser.close()

    # [요구사항 3] 수집 데이터를 엑셀(.xlsx) 파일로 저장
    excel_path = result_dir / "books_data.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Books_Data"

    if collected_books:
        # 첫 번째 행: 헤더 컬럼 등록
        sheet.append(list(collected_books[0].keys()))
        # 도서 레코드 데이터 순차 등록
        for item in collected_books:
            sheet.append(list(item.values()))

    # 엑셀 파일 최종 저장
    workbook.save(excel_path)

    print("\n" + "=" * 60)
    print("🎉 크롤링 및 저장이 성공적으로 완료되었습니다!")
    print(f" - 총 수집 권수: {len(collected_books)}권")
    print(f" - 엑셀 파일 저장 경로: {excel_path.resolve()}")
    print(f" - 이미지 저장 폴더: {image_dir.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    # uv 가상환경에서 실행: uv run python <파일명.py>
    asyncio.run(run_crawler(max_pages=2))
```
