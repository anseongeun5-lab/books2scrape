# 📚 비전공자를 위한 Playwright 웹 크롤링 완벽 입문 가이드

> **대상 사이트**: [Books to Scrape (https://books.toscrape.com/)](https://books.toscrape.com/)  
> **활용 도구**: **Playwright** (최신 웹 자동화 & 브라우저 제어 도구)  
> **문서 목적**: 프로그래밍을 깊게 알지 못해도 웹페이지의 데이터를 안전하고 쉽게 수집(크롤링)할 수 있도록 돕는 실전 가이드입니다.

---

## 1. 웹 크롤링과 Playwright란 무엇인가요?

### 1.1 웹 크롤링(Web Scraping)이란?
사람이 인터넷 브라우저를 열고, 원하는 책을 마우스로 클릭하고, 화면에 적힌 책 제목과 가격을 마우스로 드래그해서 엑셀에 일일이 복사·붙여넣기하는 작업을 **컴퓨터 로봇 비서가 대신 초고속으로 수행하도록 만드는 기술**입니다.

### 1.2 왜 Playwright(플레이라이트)를 사용할까요?
- **실제 사람처럼 행동하는 브라우저 로봇**: 마이크로소프트에서 개발한 최신 자동화 라이브러리로, 크롬(Chrome)이나 엣지(Edge) 같은 실제 브라우저를 직접 띄워서 클릭하고 스크롤합니다.
- **자바스크립트 완벽 지원**: 최신 웹사이트는 화면을 새로고침하지 않고도 동적으로 내용이 바뀌는데, Playwright는 화면이 모두 다 뜰 때까지 알아서 기다려주므로 초보자가 겪는 오류가 매우 적습니다.
- **초보자 친화적**: 코드가 직관적이며 사람이 브라우저를 조작하는 순서(페이지 열기 → 요소 찾기 → 텍스트 읽기 → 다음 페이지 클릭)와 똑같이 작성할 수 있습니다.

---

## 2. Books to Scrape 사이트에서 수집(파싱)할 수 있는 정보 총정리

Books to Scrape 사이트는 크게 **(1) 책 목록 페이지(카탈로그 화면)**와 **(2) 책 상세 페이지** 두 곳으로 구성되어 있습니다. 각각 수집할 수 있는 정보가 다릅니다.

### 2.1 📋 책 목록 페이지에서 바로 얻을 수 있는 정보 (기본 정보)

한 페이지당 20권씩 나열되어 있는 목록 화면에서 즉시 수집할 수 있는 항목들입니다.

| 수집 항목 | 설명 | 예시 데이터 | 찾는 법 (HTML 태그/선택자) |
| :--- | :--- | :--- | :--- |
| **책 제목 (Title)** | 말 줄임표(`...`) 없이 온전한 도서 전체 제목 | `A Light in the Attic` | `h3 a`의 `title` 속성값 |
| **판매 가격 (Price)** | 영국 파운드(£)로 표기된 도서 가격 | `£51.77` | `p.price_color` 태그 안의 텍스트 |
| **별점 평점 (Rating)** | 1점부터 5점까지의 고객 평점 | `Three (★ 3점)` | `p.star-rating`의 클래스명 (`Three`, `One` 등) |
| **재고 유무 (Availability)** | 현재 구매 가능한 상태인지 여부 | `In stock` | `p.instock.availability` 태그 텍스트 |
| **도서 표지 이미지 링크** | 책 표지 사진 원본 이미지 주소 | `https://books.toscrape.com/.../image.jpg` | `div.image_container img`의 `src` 속성 |
| **상세 페이지 링크** | 책의 자세한 설명을 보러 가는 웹 주소 | `catalogue/a-light-in-the-attic_1000/index.html` | `h3 a`의 `href` 속성 |

---

### 2.2 🔍 책 상세 페이지에서 추가로 얻을 수 있는 정보 (심층 정보)

각 책의 제목을 클릭하고 들어가면 나오는 상세 화면에서만 확인할 수 있는 고유 정보들입니다.

| 수집 항목 | 설명 | 예시 데이터 | 찾는 법 (HTML 태그/선택자) |
| :--- | :--- | :--- | :--- |
| **도서 카테고리 (장르)** | 책이 속한 장르 (시, 소설, 여행 등) | `Poetry` | 상단 경로(Breadcrumb) 3번째 링크 |
| **UPC (제품 고유 코드)** | 전 세계 공통 제품 식별 바코드 번호 | `a897fe39b1053632` | 제품 정보 표(`table`)의 `UPC` 행 |
| **책 상세 설명 (줄거리)** | 책의 내용 소개 및 줄거리 요약본 | `It's hard to imagine a world without...` | `Product Description` 제목 바로 아래 문단 |
| **정확한 잔여 재고 수량** | 현재 창고에 남아 있는 정확한 책 권수 | `22 available (22권 남음)` | 제품 정보 표의 `Availability` 행 |
| **세금 및 과세 정보** | 세전 가격, 세후 가격, 세금 금액 | `£0.00 (Tax)` | 제품 정보 표의 `Tax`, `Price (incl. tax)` 행 |
| **고객 리뷰 수** | 남겨진 리뷰 개수 | `0` | 제품 정보 표의 `Number of reviews` 행 |

---

## 3. 비전공자도 쉽게 이해하는 "웹 주소 찾기(CSS 선택자)" 지도

웹 크롤링의 핵심은 브라우저에게 **"저기 제목 써있는 글씨 좀 복사해와!"**라고 위치를 짚어주는 것입니다. 이 위치를 가리키는 지번 주소를 **CSS 선택자(Selector)**라고 부릅니다.

### 3.1 목록 화면 주소 지도 (Catalog Selector)
```text
도서 1권의 카드 박스전체: <article class="product_pod">
 ├── 🖼️ 이미지 사진: div.image_container img
 ├── ⭐ 별점: p.star-rating (One, Two, Three, Four, Five 클래스 포함)
 ├── 🏷️ 책 제목 및 링크: h3 a
 └── 💰 가격 & 재고:
      ├── 가격: p.price_color
      └── 재고 안내: p.instock.availability
```

### 3.2 상세 페이지 주소 지도 (Detail Selector)
```text
상세 페이지 화면:
 ├── 📂 상단 카테고리 경로: ul.breadcrumb li:nth-child(3) a
 ├── 📝 줄거리 설명: #product_description + p
 └── 📊 스펙 정보 테이블: table.table-striped
      ├── 1번째 행 (UPC): tr:nth-child(1) td
      ├── 6번째 행 (잔여 재고): tr:nth-child(6) td
      └── 7번째 행 (리뷰 수): tr:nth-child(7) td
```

> 💡 **꿀팁**: 크롬 브라우저에서 아무 글자나 마우스 우클릭 후 **[검사(Inspect)]**를 누르면, 그 글씨를 담당하는 HTML 태그를 눈으로 직접 확인할 수 있습니다.

---

## 4. 실전! Playwright로 크롤링하는 3단계 파이썬 코드

이제 실제 동작하는 파이썬 코드를 통해 크롤링을 실습해 봅니다. 모든 줄마다 친절한 한국어 인라인 주석이 작성되어 있어 그대로 읽으면서 따라 하실 수 있습니다.

### 단계 1: 필요한 도구 설치하기
터미널(PowerShell 또는 명령 프롬프트)에서 다음 명령어를 입력합니다:
```powershell
# playwright 패키지 설치
uv add playwright

# playwright가 사용할 크롬/웹킷 브라우저 엔진 자동 다운로드
uv run playwright install chromium
```

---

### 단계 2: 첫 페이지 도서 20권 수집하기 (실행 코드)

아래 코드는 브라우저를 띄워 첫 페이지에 있는 책 20권의 **제목, 가격, 별점, 재고**를 화면에 출력하는 코드입니다.

```python
"""비전공자를 위한 Playwright 도서 크롤링 기초 실습 스크립트입니다."""

import asyncio
from playwright.async_api import async_playwright

# 별점 영문 표기를 별표(★) 개수로 바꿔주는 사전 정의
STAR_RATING_MAP = {
    "One": "★☆☆☆☆ (1점)",
    "Two": "★★☆☆☆ (2점)",
    "Three": "★★★☆☆ (3점)",
    "Four": "★★★★☆ (4점)",
    "Five": "★★★★★ (5점)",
}


async def scrape_books() -> None:
    """Books to Scrape 첫 페이지의 도서들을 화면에 표시하며 수집합니다."""
    # Playwright 비동기 실행 엔진 시작
    async with async_playwright() as p:
        # 실제 크롬 브라우저 실행 (headless=False로 설정하면 화면에 뜨는 브라우저를 직접 눈으로 볼 수 있습니다)
        browser = await p.chromium.launch(headless=False, slow_mo=300)

        # 새 브라우저 탭 열기
        page = await browser.new_page()

        # 도서 웹사이트 주소로 이동
        print("[1] Books to Scrape 웹사이트에 접속합니다...")
        await page.goto("https://books.toscrape.com/")

        # 화면에 도서 카드(<article class="product_pod">)들이 모두 뜰 때까지 대기
        await page.wait_for_selector("article.product_pod")

        # 페이지에 나열된 모든 도서 카드 태그들을 한 번에 찾기
        book_cards = await page.query_selector_all("article.product_pod")
        print(f"[2] 총 {len(book_cards)}권의 도서를 발견했습니다!\n")

        # 도서 카드들을 하나씩 순회하면서 세부 데이터 추출
        for index, card in enumerate(book_cards, start=1):
            # 1. 제목 태그(h3 > a) 찾기
            title_tag = await card.query_selector("h3 a")
            # title 태그의 title 속성값(전체 제목) 읽어오기
            title = await title_tag.get_attribute("title") if title_tag else "제목 없음"

            # 2. 가격 태그(p.price_color) 찾기
            price_tag = await card.query_selector("p.price_color")
            # 가격 글씨 읽어오기 (예: £51.77)
            price = (
                (await price_tag.inner_text()).strip()
                if price_tag
                else "가격 정보 없음"
            )

            # 3. 별점 태그(p.star-rating) 클래스 속성 확인
            rating_tag = await card.query_selector("p.star-rating")
            rating_class = await rating_tag.get_attribute("class") if rating_tag else ""

            # 클래스 문자열 중 One, Two, Three 등이 있는지 검사하여 별점으로 변환
            stars = "별점 없음"
            for key, star_symbol in STAR_RATING_MAP.items():
                if key in rating_class:
                    stars = star_symbol
                    break

            # 4. 재고 상태 태그(p.instock.availability) 텍스트 확인
            stock_tag = await card.query_selector("p.instock.availability")
            stock_text = (
                (await stock_tag.inner_text()).strip() if stock_tag else "재고 미확인"
            )

            # 터미널에 보기 좋게 출력
            print(f"[{index:02d}번 도서]")
            print(f" • 제목: {title}")
            print(f" • 가격: {price}")
            print(f" • 평점: {stars}")
            print(f" • 재고: {stock_text}")
            print("-" * 50)

        # 모든 작업이 끝나면 브라우저를 닫아 컴퓨터 메모리 정리
        print("[3] 수집이 완료되어 브라우저를 닫습니다.")
        await browser.close()


if __name__ == "__main__":
    # 비동기 함수 실행 시작
    asyncio.run(scrape_books())
```

---

### 단계 3: 수집한 데이터를 엑셀(CSV) 파일로 저장하기

수집한 도서 목록을 `scraping_result` 폴더 안의 `books_playwright.csv` 파일로 깔끔하게 저장하는 완성형 코드입니다.

```python
"""수집한 도서 목록을 CSV 파일로 저장하는 완성형 Playwright 크롤러입니다."""

import asyncio
import csv
from pathlib import Path
from playwright.async_api import async_playwright


async def run_crawler_and_save_csv() -> None:
    """도서 목록을 크롤링하여 CSV 파일로 저장합니다."""
    # 결과물을 저장할 폴더 경로 설정
    result_folder = Path("scraping_result")
    # 폴더가 없으면 컴퓨터에 새로 생성
    result_folder.mkdir(parents=True, exist_ok=True)
    # 최종 저장될 파일 경로 (CSV)
    csv_file_path = result_folder / "books_playwright.csv"

    # 수집한 책 정보들을 담을 리스트 바구니
    collected_books = []

    async with async_playwright() as p:
        # 화면 없이 백그라운드에서 빠르게 동작하도록 headless=True 지정
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("[*] 웹페이지 접속 중...")
        await page.goto("https://books.toscrape.com/")

        # 도서 카드 목록 가져오기
        cards = await page.query_selector_all("article.product_pod")

        for card in cards:
            title_elem = await card.query_selector("h3 a")
            title = await title_elem.get_attribute("title") if title_elem else ""

            price_elem = await card.query_selector("p.price_color")
            price = (
                (await price_elem.inner_text()).replace("£", "").strip()
                if price_elem
                else "0.0"
            )

            # 상세 링크 URL 가져오기
            link_elem = await card.query_selector("h3 a")
            rel_link = await link_elem.get_attribute("href") if link_elem else ""
            full_link = f"https://books.toscrape.com/{rel_link}"

            # 딕셔너리 형태로 한 권의 정보 정리
            collected_books.append(
                {
                    "도서제목": title,
                    "가격(파운드)": price,
                    "상세페이지링크": full_link,
                }
            )

        await browser.close()

    # 엑셀과 호환성이 좋은 utf-8-sig 인코딩으로 CSV 파일 작성
    with open(csv_file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["도서제목", "가격(파운드)", "상세페이지링크"]
        )
        # 컬럼 이름(헤더) 쓰기
        writer.writeheader()
        # 책 목록 데이터 기록하기
        writer.writerows(collected_books)

    print(
        f"[성공] 총 {len(collected_books)}권의 도서 정보가 '{csv_file_path}'에 저장되었습니다!"
    )


if __name__ == "__main__":
    asyncio.run(run_crawler_and_save_csv())
```

---

## 5. 다음 페이지로 자동 이동하기 (페이지네이션)

Books to Scrape는 총 50페이지(1,000권)의 책이 있습니다. 다음 페이지로 넘어가려면 하단의 **"next"** 버튼을 눌러야 합니다.

Playwright에서는 마우스 클릭을 코드로 아래와 같이 아주 쉽게 구현할 수 있습니다:

```python
# 'next' 버튼(<li class="next a">)이 페이지에 존재하는지 확인
next_button = await page.query_selector("li.next a")

if next_button:
    # 다음 페이지 버튼 마우스 클릭!
    await next_button.click()
    # 페이지가 완전히 로딩될 때까지 잠시 대기
    await page.wait_for_load_state("networkidle")
else:
    # 다음 버튼이 없으면 마지막 페이지에 도달한 것이므로 크롤링 종료
    print("마지막 페이지에 도달했습니다.")
```

---

## 6. 비전공자를 위한 웹 크롤링 주의사항 & 매너 (에티켓)

1. **너무 빠르게 광클(DDoS 수준의 요청)하지 마세요**:
   - 사람이 웹페이지를 둘러보듯 최소 **0.5초 ~ 1초 정도의 대기 시간(Delay)**을 주는 것이 사이트 서버에 부담을 주지 않는 좋은 매너입니다.
   - 예: `await page.wait_for_timeout(1000)` (1초 대기)
2. **저작권 및 개인정보 주의**:
   - Books to Scrape는 스크래핑 연습용으로 공개된 안전한 샌드박스 사이트이지만, 실제 상용 사이트에서는 이용약관(robots.txt)을 반드시 확인해야 합니다.
3. **선택자가 깨질 수 있습니다**:
   - 웹사이트 리뉴얼이나 디자인 개편이 일어나면 태그 이름이 바뀔 수 있습니다. 만약 데이터가 빈 값으로 나온다면 브라우저 [검사] 창을 열어 태그 이름을 다시 확인해 보세요.

