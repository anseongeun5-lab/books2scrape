"""books2scrape 메인 진입점 및 CLI 모듈입니다."""

import argparse
import sys
from pathlib import Path

from books2scrape.database import BookDatabase
from books2scrape.downloader import download_book_images
from books2scrape.exporter import export_books
from books2scrape.scraper import BookScraper


def get_greeting() -> str:
    """기본 안내 메시지를 반환합니다."""
    # 프로젝트 기본 인사말 및 시작 안내 메시지 반환
    return "Books to Scrape 프로젝트 환경이 성공적으로 설정되었습니다."


def parse_cli_args(args: list[str] | None = None) -> argparse.Namespace:
    """CLI 실행 인자를 정의하고 파싱합니다."""
    # argparse 객체 초기화
    parser = argparse.ArgumentParser(
        description="Books to Scrape 사이트 도서 데이터 수집 CLI 도구"
    )

    # 수집할 최대 페이지 수 인자
    parser.add_argument(
        "--pages",
        "-p",
        type=int,
        default=1,
        help="스크래핑할 최대 페이지 수 (기본값: 1)",
    )

    # 특정 카테고리 필터링 인자
    parser.add_argument(
        "--category",
        "-c",
        type=str,
        default=None,
        help="특정 카테고리 도서만 수집 (예: 'Poetry', 'Travel', 'Mystery')",
    )

    # 지원되는 카테고리 목록 출력 플래그
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="웹사이트에서 지원하는 전체 카테고리 목록을 조회하여 출력",
    )

    # 결과물 출력 경로 인자
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="books.csv",
        help="저장할 파일 경로 (.csv 또는 .json 확장자 지원, 기본값: books.csv)",
    )

    # 상세 페이지 세부 수집 활성화 플래그
    parser.add_argument(
        "--detail",
        "-d",
        action="store_true",
        help="도서 상세 페이지를 방문하여 카테고리, UPC, 설명까지 추가 수집",
    )

    # 표지 이미지 다운로드 활성화 플래그
    parser.add_argument(
        "--download-images",
        action="store_true",
        help="수집된 도서의 표지 이미지 파일들을 로컬 폴더(images/)에 다운로드",
    )

    # SQLite 데이터베이스 저장 플래그
    parser.add_argument(
        "--save-db",
        action="store_true",
        help="수집된 도서 데이터를 SQLite DB(books.db)에도 함께 영구 저장",
    )

    # 셀레늄 웹드라이버 모드 사용 플래그
    parser.add_argument(
        "--use-selenium",
        action="store_true",
        help="고속 HTTPX 대신 셀레늄(Chrome Headless) 웹드라이버를 사용하여 수집",
    )

    # 파싱된 네임스페이스 반환
    return parser.parse_args(args)


def main() -> None:
    """CLI 메인 진입점 함수입니다."""
    # 명령행 인자 파싱 (sys.argv[1:])
    args = parse_cli_args(sys.argv[1:])

    # 스크래퍼 컨텍스트 매니저 실행
    with BookScraper(use_selenium=args.use_selenium) as scraper:
        # 1. 카테고리 목록 조회 요청인 경우
        if args.list_categories:
            print("[*] 지원되는 도서 카테고리 목록을 조회합니다...")
            categories = scraper.fetch_categories()
            print(f"\n총 {len(categories)}개의 카테고리가 등록되어 있습니다:")
            for idx, name in enumerate(sorted(categories.keys()), start=1):
                print(f" {idx:2d}. {name}")
            return

        # 시작 안내 문구 출력
        print("=" * 60)
        print("📚 Books to Scrape 웹 스크래퍼 실행")
        if args.category:
            print(f" - 선택 카테고리: {args.category}")
        print(f" - 최대 수집 페이지: {args.pages} 페이지")
        print(f" - 상세 정보 수집 여부: {'활성화' if args.detail else '비활성화'}")
        print(
            f" - 스크래핑 엔진: {'Selenium Chrome' if args.use_selenium else 'HTTPX + BeautifulSoup'}"
        )
        print(f" - 파일 저장 경로: {args.output}")
        if args.save_db:
            print(" - SQLite DB 저장: 활성화 (books.db)")
        if args.download_images:
            print(" - 이미지 다운로드: 활성화 (scraping_result/images/)")
        print("=" * 60)

        # 카테고리 지정 여부에 따른 분기 수집
        if args.category:
            books = scraper.scrape_category(
                category_name=args.category,
                max_pages=args.pages,
                fetch_details=args.detail,
            )
        else:
            books = scraper.scrape_all(
                max_pages=args.pages,
                fetch_details=args.detail,
            )

    # 수집된 도서 수 확인
    total_count = len(books)
    print(f"\n[+] 총 {total_count}권의 도서 데이터를 성공적으로 수집했습니다.")

    if total_count > 0:
        # 1. 지정된 경로로 파일 내보내기 (CSV 또는 JSON)
        output_path = Path(args.output)
        saved_path = export_books(books, output_path)
        print(f"[+] 파일 저장 완료: {saved_path.resolve()}")

        # 2. SQLite 데이터베이스에 UPSERT 저장 (옵션 활성화 시)
        if args.save_db:
            db = BookDatabase("books.db")
            upserted_count = db.upsert_books(books)
            print(
                f"[+] SQLite DB 저장 완료: {upserted_count}권 (총 보관 도서: {db.count()}권)"
            )

        # 3. 도서 표지 이미지 다운로드 실행 (옵션 활성화 시)
        if args.download_images:
            img_dir = output_path.parent / "images"
            print(f"[*] 표지 이미지 다운로드 시작 -> {img_dir.resolve()}")
            downloaded_files = download_book_images(books, output_dir=img_dir)
            print(f"[+] 표지 이미지 다운로드 완료: 총 {len(downloaded_files)}개 저장됨")
    else:
        print("[-] 수집된 데이터가 없습니다.")


if __name__ == "__main__":
    # 스크립트 직접 실행 시 main 함수 호출
    main()
