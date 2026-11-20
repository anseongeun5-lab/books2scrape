"""스크래퍼 파싱 함수, 데이터베이스, 이미지 유틸에 대한 단위 테스트 모듈입니다."""

from pathlib import Path

from bs4 import BeautifulSoup

from books2scrape.database import BookDatabase
from books2scrape.downloader import sanitize_filename
from books2scrape.exporter import export_books, save_to_csv, save_to_json
from books2scrape.models import BookItem
from books2scrape.scraper import (
    parse_catalog_page_html,
    parse_categories_html,
    parse_detail_page_html,
    parse_price,
    parse_rating,
    parse_stock_count,
)

# 단위 테스트용 카탈로그 목록 HTML 목업 데이터 정의
MOCK_CATALOG_HTML = """
<ol class="row">
    <li class="col-xs-6 col-sm-4 col-md-3 col-lg-3">
        <article class="product_pod">
            <div class="image_container">
                <a href="catalogue/a-light-in-the-attic_1000/index.html">
                    <img src="media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg" alt="A Light in the Attic" class="thumbnail">
                </a>
            </div>
            <p class="star-rating Three">
                <i class="icon-star"></i>
            </p>
            <h3>
                <a href="catalogue/a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in the Attic</a>
            </h3>
            <div class="product_price">
                <p class="price_color">£51.77</p>
                <p class="instock availability">
                    <i class="icon-ok"></i>
                    In stock
                </p>
            </div>
        </article>
    </li>
    <li class="col-xs-6 col-sm-4 col-md-3 col-lg-3">
        <article class="product_pod">
            <div class="image_container">
                <a href="catalogue/tipping-the-velvet_999/index.html">
                    <img src="media/cache/26/0c/260c6ae16bce31c8f8c95daddd9f4a1c.jpg" alt="Tipping the Velvet" class="thumbnail">
                </a>
            </div>
            <p class="star-rating One">
                <i class="icon-star"></i>
            </p>
            <h3>
                <a href="catalogue/tipping-the-velvet_999/index.html" title="Tipping the Velvet">Tipping the Velvet</a>
            </h3>
            <div class="product_price">
                <p class="price_color">£53.74</p>
                <p class="instock availability">
                    <i class="icon-ok"></i>
                    In stock
                </p>
            </div>
        </article>
    </li>
</ol>
"""

# 단위 테스트용 상세 페이지 HTML 목업 데이터 정의
MOCK_DETAIL_HTML = """
<ul class="breadcrumb">
    <li><a href="../../index.html">Home</a></li>
    <li><a href="../category/books_1/index.html">Books</a></li>
    <li><a href="../category/books/poetry_23/index.html">Poetry</a></li>
    <li class="active">A Light in the Attic</li>
</ul>
<div id="product_description" class="sub-header">
    <h2>Product Description</h2>
</div>
<p>It's hard to imagine a world without A Light in the Attic.</p>
<table class="table table-striped">
    <tr><th>UPC</th><td>a897fe39b1053632</td></tr>
    <tr><th>Product Type</th><td>Books</td></tr>
    <tr><th>Price (excl. tax)</th><td>£51.77</td></tr>
    <tr><th>Price (incl. tax)</th><td>£51.77</td></tr>
    <tr><th>Tax</th><td>£0.00</td></tr>
    <tr><th>Availability</th><td>In stock (22 available)</td></tr>
    <tr><th>Number of reviews</th><td>0</td></tr>
</table>
"""

# 단위 테스트용 사이드바 카테고리 HTML 목업 데이터 정의
MOCK_SIDEBAR_HTML = """
<div class="side_categories">
    <ul class="nav nav-list">
        <li>
            <a href="catalogue/category/books_1/index.html">Books</a>
            <ul>
                <li><a href="catalogue/category/books/travel_2/index.html">Travel</a></li>
                <li><a href="catalogue/category/books/mystery_3/index.html">Mystery</a></li>
                <li><a href="catalogue/category/books/poetry_23/index.html">Poetry</a></li>
            </ul>
        </li>
    </ul>
</div>
"""


def test_parse_price() -> None:
    """가격 문자열에서 정상적으로 float 값을 추출하는지 검증합니다."""
    # 통화 기호가 포함된 가격 변환 테스트
    assert parse_price("£51.77") == 51.77
    # 달러 기호 가격 변환 테스트
    assert parse_price("$19.99") == 19.99
    # 잘못된 형식일 때 0.0 반환 여부 테스트
    assert parse_price("Free") == 0.0


def test_parse_rating() -> None:
    """별점 태그 클래스로부터 1~5 정수 평점을 정확히 계산하는지 검증합니다."""
    # 3점 태그 파싱 검증
    soup = BeautifulSoup('<p class="star-rating Three"></p>', "lxml")
    assert parse_rating(soup.find("p")) == 3

    # 5점 태그 파싱 검증
    soup5 = BeautifulSoup('<p class="star-rating Five"></p>', "lxml")
    assert parse_rating(soup5.find("p")) == 5

    # 클래스가 누락되었거나 존재하지 않는 태그일 경우 0점 반환 검증
    assert parse_rating(None) == 0


def test_parse_stock_count() -> None:
    """재고 안내 문구에서 재고 수량을 올바르게 추출하는지 검증합니다."""
    # 22 available 패턴 추출 검증
    assert parse_stock_count("In stock (22 available)") == 22
    # 수량 정보가 없을 경우 0 반환 검증
    assert parse_stock_count("In stock") == 0


def test_parse_catalog_page_html() -> None:
    """카탈로그 HTML에서 도서 목록 2권이 정상 추출되는지 검증합니다."""
    # 카탈로그 HTML 파싱 수행
    books = parse_catalog_page_html(
        MOCK_CATALOG_HTML, current_page_url="https://books.toscrape.com/index.html"
    )

    # 2권 추출 여부 확인
    assert len(books) == 2

    # 첫 번째 도서의 상세 속성 검증
    first = books[0]
    assert first.title == "A Light in the Attic"
    assert first.price == 51.77
    assert first.rating == 3
    assert first.in_stock is True
    assert (
        first.detail_url
        == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    )


def test_parse_detail_page_html() -> None:
    """상세 페이지 HTML에서 카테고리, UPC, 설명 등이 정상 추출되는지 검증합니다."""
    # 상세 페이지 파싱 수행
    details = parse_detail_page_html(MOCK_DETAIL_HTML)

    # 카테고리 추출 검증
    assert details["category"] == "Poetry"
    # UPC 코드 추출 검증
    assert details["upc"] == "a897fe39b1053632"
    # 재고 수량 추출 검증
    assert details["stock_count"] == 22
    # 도서 설명 추출 검증
    assert "without A Light in the Attic" in details["description"]


def test_parse_categories_html() -> None:
    """사이드바 HTML에서 카테고리 이름과 절대 URL 매핑이 정상 추출되는지 검증합니다."""
    # 카테고리 파싱 수행
    cat_map = parse_categories_html(
        MOCK_SIDEBAR_HTML, base_url="https://books.toscrape.com/"
    )

    # 파싱된 카테고리 수 확인
    assert len(cat_map) == 3
    # 카테고리 키 존재 여부 확인
    assert "Travel" in cat_map
    assert "Mystery" in cat_map
    assert "Poetry" in cat_map
    # 절대 URL 변환 여부 검증
    assert (
        cat_map["Travel"]
        == "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"
    )


def test_sanitize_filename() -> None:
    """특수문자가 포함된 도서 제목이 안전한 파일명으로 정제되는지 검증합니다."""
    # 콜론, 슬래시, 쉼표 등이 포함된 문자열 테스트
    raw_name = "Book: Title / Subtitle ? <New>"
    sanitized = sanitize_filename(raw_name)
    # 특수문자 제거 확인
    assert ":" not in sanitized
    assert "/" not in sanitized
    assert "?" not in sanitized
    assert "<" not in sanitized


def test_export_functions(tmp_path: Path) -> None:
    """CSV 및 JSON 내보내기 함수가 정상 동작하는지 검증합니다."""
    # 테스트용 도서 인스턴스 생성
    dummy_book = BookItem(
        title="Test Book",
        price=10.5,
        rating=4,
        availability="In stock",
        in_stock=True,
        stock_count=5,
        detail_url="https://books.toscrape.com/test",
        image_url="https://books.toscrape.com/test.jpg",
        category="Test",
        upc="123456789",
        description="Test description",
    )

    # 임시 CSV 파일 저장 테스트
    csv_file = tmp_path / "test.csv"
    save_to_csv([dummy_book], csv_file)
    assert csv_file.exists()
    assert "Test Book" in csv_file.read_text(encoding="utf-8-sig")

    # 임시 JSON 파일 저장 테스트
    json_file = tmp_path / "test.json"
    save_to_json([dummy_book], json_file)
    assert json_file.exists()
    assert "Test Book" in json_file.read_text(encoding="utf-8")

    # 자동 포맷 분기 export_books 테스트
    auto_csv = tmp_path / "auto.csv"
    export_books([dummy_book], auto_csv)
    assert auto_csv.exists()


def test_sqlite_database(tmp_path: Path) -> None:
    """SQLite 데이터베이스 생성, UPSERT 및 조회가 정상 동작하는지 검증합니다."""
    db_file = tmp_path / "test_books.db"
    db = BookDatabase(db_file)

    # 도서 데이터 1건 생성
    book1 = BookItem(
        title="DB Test Book",
        price=25.0,
        rating=5,
        availability="In stock (10 available)",
        in_stock=True,
        stock_count=10,
        detail_url="https://books.toscrape.com/db_test_1",
        image_url="https://books.toscrape.com/img1.jpg",
        category="Testing",
        upc="UPC123456",
        description="Initial description",
    )

    # DB 삽입 테스트
    count = db.upsert_books([book1])
    assert count == 1
    assert db.count() == 1

    # 동일 detail_url로 가격 업데이트(UPSERT) 테스트
    book1_updated = book1.model_copy(update={"price": 29.99})
    db.upsert_books([book1_updated])
    # 레코드 수는 그대로 1개여야 함
    assert db.count() == 1

    # 데이터 조회 및 가격 업데이트 확인
    books_in_db = db.get_books_by_category("Testing")
    assert len(books_in_db) == 1
    assert books_in_db[0]["price"] == 29.99
    assert books_in_db[0]["upc"] == "UPC123456"
