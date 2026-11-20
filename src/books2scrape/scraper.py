"""Books to Scrape 웹사이트 크롤링 및 데이터 파싱을 담당하는 스크래퍼 모듈입니다."""

import re
from typing import Any, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from books2scrape.config import (
    BASE_URL,
    CATALOGUE_PAGE_URL,
    DEFAULT_HEADERS,
    DEFAULT_TIMEOUT,
    RATING_MAP,
)
from books2scrape.models import BookItem


def parse_rating(rating_element: Optional[Tag]) -> int:
    """별점 태그 클래스로부터 1~5 정수 평점을 추출합니다."""
    # 태그가 없으면 0점 반환
    if not rating_element:
        return 0
    # 태그의 모든 CSS 클래스명을 소문자로 추출
    classes = [c.lower() for c in rating_element.get("class", [])]
    # RATING_MAP 사전에 정의된 단어가 클래스에 포함되어 있는지 검색
    for name, score in RATING_MAP.items():
        if name in classes:
            # 일치하는 별점 점수 반환
            return score
    # 매칭 실패 시 기본값 0 반환
    return 0


def parse_price(price_text: str) -> float:
    """가격 문자열(예: '£51.77')에서 화폐 기호를 제거하고 float 형태로 변환합니다."""
    # 정규표현식을 사용하여 숫자와 소수점만 추출
    match = re.search(r"([0-9]+\.[0-9]+)", price_text)
    if match:
        # 추출된 숫자 문자열을 부동소수점형으로 변환하여 반환
        return float(match.group(1))
    # 가격 파싱 실패 시 0.0 반환
    return 0.0


def parse_stock_count(availability_text: str) -> int:
    """재고 안내 문구(예: 'In stock (22 available)')에서 수량 숫자를 추출합니다."""
    # 괄호 안의 숫자 패턴 검색
    match = re.search(r"\((\d+)\s+available\)", availability_text)
    if match:
        # 추출한 수량 숫자를 정수로 변환
        return int(match.group(1))
    # 구체적인 수량이 없을 경우 0 반환
    return 0


def parse_book_card(pod: Tag, current_page_url: str = BASE_URL) -> Optional[BookItem]:
    """도서 목록 카드의 단일 HTML 태그(<article class='product_pod'>)에서 도서 기본 정보를 추출합니다."""
    # 제목 링크 태그(h3 > a) 검색
    title_tag = pod.select_one("h3 a")
    if not title_tag:
        # 필수 요소인 제목 태그가 없으면 None 반환
        return None

    # title 속성값이 있으면 전체 제목으로 채택하고, 없으면 a 태그의 텍스트 채택
    raw_title = title_tag.get("title") or title_tag.get_text(strip=True)

    # 상세 페이지 상대 경로 획득
    relative_link = title_tag.get("href", "")
    # 상대 경로를 현재 페이지 기준 절대 URL로 완성
    detail_url = urljoin(current_page_url, relative_link)

    # 표지 이미지 태그 검색
    image_tag = pod.select_one("div.image_container img")
    image_relative = image_tag.get("src", "") if image_tag else ""
    # 이미지 상대 경로를 절대 URL로 완성
    image_url = urljoin(current_page_url, image_relative)

    # 별점 태그 검색
    rating_tag = pod.select_one("p.star-rating")
    # 별점 점수 파싱
    rating = parse_rating(rating_tag)

    # 가격 태그 검색
    price_tag = pod.select_one("p.price_color")
    price_text = price_tag.get_text(strip=True) if price_tag else "£0.00"
    # 가격 숫자 변환
    price = parse_price(price_text)

    # 재고 상태 태그 검색
    avail_tag = pod.select_one("p.instock.availability")
    avail_text = avail_tag.get_text(strip=True) if avail_tag else ""
    # 'In stock' 문구가 포함되어 있는지 확인하여 재고 유무 결정
    in_stock = "in stock" in avail_text.lower()

    # 파싱된 정보를 기반으로 BookItem 데이터 모델 인스턴스 생성
    return BookItem(
        title=raw_title,
        price=price,
        rating=rating,
        availability=avail_text,
        in_stock=in_stock,
        detail_url=detail_url,
        image_url=image_url,
    )


def parse_catalog_page_html(
    html: str, current_page_url: str = BASE_URL
) -> list[BookItem]:
    """카탈로그 목록 페이지의 전체 HTML 소스를 파싱하여 도서 객체 목록을 반환합니다."""
    # 뷰티풀스프 객체 생성 (lxml 파서 사용)
    soup = BeautifulSoup(html, "lxml")
    # 도서 카드들을 포함하는 모든 article 태그 검색
    pods = soup.select("article.product_pod")

    # 수집 결과를 담을 리스트 초기화
    books: list[BookItem] = []
    for pod in pods:
        # 개별 도서 카드 파싱 시도
        item = parse_book_card(pod, current_page_url=current_page_url)
        if item:
            # 정상 파싱된 도서 객체를 목록에 추가
            books.append(item)

    # 수집 완료된 도서 목록 반환
    return books


def parse_categories_html(html: str, base_url: str = BASE_URL) -> dict[str, str]:
    """웹사이트 좌측 사이드바에서 지원하는 전체 도서 카테고리와 링크 맵을 추출합니다."""
    soup = BeautifulSoup(html, "lxml")
    # 사이드바 카테고리 링크 검색 (div.side_categories 내부 ul.nav-list ul li a)
    links = soup.select(".side_categories ul.nav-list > li > ul > li > a")

    category_map: dict[str, str] = {}
    for link in links:
        # 공백 제거된 카테고리 이름
        name = link.get_text(strip=True)
        href = link.get("href", "")
        if name and href:
            # 상대 경로를 완전한 절대 URL로 완성
            full_url = urljoin(base_url, href)
            category_map[name] = full_url

    # 추출된 카테고리 딕셔너리 반환
    return category_map


def parse_detail_page_html(html: str) -> dict[str, Any]:
    """개별 도서 상세 페이지의 HTML을 파싱하여 세부 정보(카테고리, UPC, 설명 등)를 딕셔너리로 반환합니다."""
    # 뷰티풀스프 객체 생성
    soup = BeautifulSoup(html, "lxml")
    details: dict[str, Any] = {}

    # 빵부스러기(Breadcrumb) 네비게이션에서 카테고리 추출 (Home > Books > [Category] > Title)
    category_elem = soup.select_one("ul.breadcrumb li:nth-child(3) a")
    if category_elem:
        # 카테고리명 설정
        details["category"] = category_elem.get_text(strip=True)

    # 제품 설명(Description) 추출 (#product_description 바로 다음의 p 태그)
    desc_header = soup.select_one("#product_description")
    if desc_header:
        # 바로 다음 형제 p 태그 검색
        desc_p = desc_header.find_next_sibling("p")
        if desc_p:
            # 상세 설명 텍스트 저장
            details["description"] = desc_p.get_text(strip=True)

    # 하단 제품 정보 테이블(table.table-striped)에서 속성값들 추출
    table_rows = soup.select("table.table-striped tr")
    for row in table_rows:
        # 속성명 헤더 태그 추출
        th = row.select_one("th")
        # 속성값 데이터 태그 추출
        td = row.select_one("td")
        if not th or not td:
            # 필수 태그가 없으면 다음 행으로 건너뜀
            continue

        header_name = th.get_text(strip=True).lower()
        val_text = td.get_text(strip=True)

        if "upc" in header_name:
            # UPC 고유 코드 저장
            details["upc"] = val_text
        elif "availability" in header_name:
            # 상세 재고 문구 및 수량 파싱
            details["stock_count"] = parse_stock_count(val_text)
            details["availability"] = val_text

    # 파싱된 세부 정보 딕셔너리 반환
    return details


class BookScraper:
    """HTTP 요청 및 브라우저 제어를 통해 Books to Scrape 웹사이트를 스크래핑하는 메인 클래스입니다."""

    def __init__(self, use_selenium: bool = False, timeout: float = DEFAULT_TIMEOUT):
        """스크래퍼 인스턴스를 초기화합니다."""
        # 동적 렌더링 셀레늄 사용 여부 플래그 저장
        self.use_selenium = use_selenium
        # 요청 타임아웃 시간 저장
        self.timeout = timeout
        # 재사용 가능한 HTTPX 클라이언트 초기화
        self._client: Optional[httpx.Client] = None
        # 셀레늄 웹드라이버 인스턴스 (필요 시 생성)
        self._driver: Optional[webdriver.Chrome] = None

    def __enter__(self) -> "BookScraper":
        """컨텍스트 매니저 진입 시 리소스를 초기화합니다."""
        if self.use_selenium:
            # 셀레늄 헤드리스 브라우저 옵션 설정
            chrome_options = Options()
            # UI 창 없이 백그라운드에서 실행되도록 헤드리스 모드 활성화
            chrome_options.add_argument("--headless=new")
            # 리눅스/샌드박스 환경 충돌 방지 옵션
            chrome_options.add_argument("--no-sandbox")
            # 메모리 공유 제한 해제
            chrome_options.add_argument("--disable-dev-shm-usage")
            # 가상 User-Agent 등록
            chrome_options.add_argument(f"user-agent={DEFAULT_HEADERS['User-Agent']}")
            # 크롬 웹드라이버 기동
            self._driver = webdriver.Chrome(options=chrome_options)
        else:
            # 고속 HTTP 요청을 위한 httpx Client 초기화
            self._client = httpx.Client(
                headers=DEFAULT_HEADERS,
                timeout=self.timeout,
                follow_redirects=True,
            )
        # 자기 자신 객체 반환
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """컨텍스트 매니저 종료 시 리소스를 안전하게 닫습니다."""
        if self._client:
            # HTTP 클라이언트 종료
            self._client.close()
            self._client = None
        if self._driver:
            # 셀레늄 웹드라이버 프로세스 종료
            self._driver.quit()
            self._driver = None

    def fetch_html(self, url: str) -> str:
        """지정된 URL의 웹페이지 HTML을 다운로드하여 반환합니다."""
        if self.use_selenium and self._driver:
            # 셀레늄 드라이버로 페이지 이동
            self._driver.get(url)
            # 브라우저에 렌더링된 소스 반환
            return self._driver.page_source

        # HTTP 클라이언트가 미생성된 경우 임시 생성
        client = self._client or httpx.Client(
            headers=DEFAULT_HEADERS, timeout=self.timeout, follow_redirects=True
        )
        try:
            # GET 요청 전송
            response = client.get(url)
            # HTTP 200번대 응답 여부 검증
            response.raise_for_status()
            # 응답 텍스트 반환
            return response.text
        finally:
            if not self._client:
                # 임시 클라이언트인 경우 종료
                client.close()

    def fetch_categories(self) -> dict[str, str]:
        """웹사이트 메인 페이지에서 지원되는 카테고리 목록과 링크를 조회합니다."""
        # 메인 페이지 HTML 요청
        html = self.fetch_html(BASE_URL)
        # 사이드바 카테고리 파싱 결과 반환
        return parse_categories_html(html, base_url=BASE_URL)

    def scrape_catalog_page(self, page: int = 1) -> list[BookItem]:
        """특정 카탈로그 페이지의 도서들을 스크래핑합니다."""
        # 1페이지와 그 외 페이지의 URL 구성 분기
        if page == 1:
            target_url = "https://books.toscrape.com/catalogue/page-1.html"
        else:
            target_url = CATALOGUE_PAGE_URL.format(page=page)

        try:
            # 해당 페이지 HTML 가져오기
            html = self.fetch_html(target_url)
            # HTML 파싱하여 도서 목록 추출
            return parse_catalog_page_html(html, current_page_url=target_url)
        except httpx.HTTPStatusError as e:
            # 404 등 없는 페이지 도달 시 빈 목록 반환하여 페이징 종료 처리
            if e.response.status_code == 404:
                return []
            # 기타 HTTP 오류는 상위로 전파
            raise

    def enrich_book_detail(self, book: BookItem) -> BookItem:
        """도서의 상세 페이지를 방문하여 추가 메타데이터(설명, UPC 등)를 보강합니다."""
        # 상세 페이지 HTML 요청
        detail_html = self.fetch_html(book.detail_url)
        # 상세 정보 파싱
        details = parse_detail_page_html(detail_html)

        # 기존 객체를 업데이트한 새로운 모델 인스턴스 복제 및 반환
        return book.model_copy(update=details)

    def scrape_category(
        self,
        category_name: str,
        max_pages: int = 1,
        fetch_details: bool = False,
    ) -> list[BookItem]:
        """특정 카테고리에 속한 도서 목록을 수집합니다."""
        # 전체 카테고리 맵 조회
        categories = self.fetch_categories()
        # 대소문자 무관 비교를 위한 사전 생성
        lookup = {k.lower(): (k, v) for k, v in categories.items()}

        cat_key = category_name.strip().lower()
        if cat_key not in lookup:
            available_names = ", ".join(list(categories.keys())[:10])
            raise ValueError(
                f"존재하지 않는 카테고리입니다: '{category_name}'. (예시: {available_names}...)"
            )

        official_name, category_base_url = lookup[cat_key]
        print(f"[*] 카테고리 '{official_name}' 수집 시작...")

        all_books: list[BookItem] = []
        # 카테고리 1페이지 URL
        current_url: Optional[str] = category_base_url

        page_count = 0
        while current_url and page_count < max_pages:
            page_count += 1
            print(f"[*] 카테고리 페이지 {page_count} 수집 중...")
            html = self.fetch_html(current_url)
            page_books = parse_catalog_page_html(html, current_page_url=current_url)

            if not page_books:
                break

            for book in page_books:
                # 카테고리명 미리 주입
                book.category = official_name
                if fetch_details:
                    try:
                        book = self.enrich_book_detail(book)
                    except Exception as err:
                        print(f"[경고] 상세 수집 실패 ({book.title}): {err}")
                all_books.append(book)

            # 다음 페이지(li.next a) 링크 확인
            soup = BeautifulSoup(html, "lxml")
            next_tag = soup.select_one("li.next a")
            if next_tag and next_tag.get("href"):
                current_url = urljoin(current_url, next_tag["href"])
            else:
                current_url = None

        return all_books

    def scrape_all(
        self,
        max_pages: int = 1,
        fetch_details: bool = False,
    ) -> list[BookItem]:
        """지정한 페이지 범위까지 순회하며 전체 도서 목록을 수집합니다."""
        all_books: list[BookItem] = []

        # 1페이지부터 max_pages까지 순차 탐색
        for page in range(1, max_pages + 1):
            print(f"[*] 페이지 {page} 수집 중...")
            # 현재 페이지 도서 목록 획득
            page_books = self.scrape_catalog_page(page)
            # 더 이상 도서가 없으면 루프 탈출
            if not page_books:
                print(f"[!] {page}페이지에서 더 이상의 도서를 찾을 수 없습니다.")
                break

            for item in page_books:
                if fetch_details:
                    try:
                        # 상세 페이지 정보 보강
                        item = self.enrich_book_detail(item)
                    except Exception as err:
                        # 상세 페이지 수집 실패 시 로그 출력 후 기본 정보 유지
                        print(f"[경고] '{item.title}' 상세 수집 실패: {err}")
                # 전체 목록에 도서 항목 추가
                all_books.append(item)

        # 수집 완료된 전체 리스트 반환
        return all_books
