"""SQLite를 활용하여 도서 데이터를 로컬 데이터베이스에 저장하고 관리하는 모듈입니다."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

from books2scrape.models import BookItem


class BookDatabase:
    """수집된 도서 데이터를 SQLite DB 파일에 저장하고 조회하는 데이터베이스 헬퍼 클래스입니다."""

    def __init__(self, db_path: Path | str = "books.db"):
        """데이터베이스 연결 경로를 설정합니다."""
        # 파일 경로 객체로 변환
        self.db_path = Path(db_path)
        # 상위 디렉터리 자동 생성
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # 테이블 자동 초기화
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """SQLite 데이터베이스 연결 객체를 생성하고 컬럼명 기반 접근(Row factory)을 설정합니다."""
        conn = sqlite3.connect(self.db_path)
        # 결과 레코드를 딕셔너리처럼 접근할 수 있도록 row_factory 지정
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """도서 저장을 위한 기본 테이블 및 인덱스를 생성합니다."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # books 테이블 생성 쿼리 (detail_url을 고유 키로 활용하여 UPSERT 지원)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    detail_url TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    price REAL NOT NULL,
                    rating INTEGER DEFAULT 0,
                    availability TEXT,
                    in_stock INTEGER DEFAULT 1,
                    stock_count INTEGER DEFAULT 0,
                    image_url TEXT,
                    category TEXT DEFAULT 'Unknown',
                    upc TEXT,
                    description TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            # 빠른 조회를 위해 카테고리 인덱스 추가
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_books_category ON books(category)"
            )
            # 변경 사항 커밋
            conn.commit()

    def upsert_books(self, books: Sequence[BookItem]) -> int:
        """도서 목록을 DB에 삽입하거나, 이미 존재하는 경우 최신 데이터로 업데이트(UPSERT)합니다."""
        if not books:
            return 0

        # 현재 UTC 시각을 ISO 포맷 문자열로 기록
        now_str = datetime.now(timezone.utc).isoformat()
        upsert_query = """
            INSERT INTO books (
                detail_url, title, price, rating, availability, in_stock,
                stock_count, image_url, category, upc, description, updated_at
            ) VALUES (
                :detail_url, :title, :price, :rating, :availability, :in_stock,
                :stock_count, :image_url, :category, :upc, :description, :updated_at
            )
            ON CONFLICT(detail_url) DO UPDATE SET
                title = excluded.title,
                price = excluded.price,
                rating = excluded.rating,
                availability = excluded.availability,
                in_stock = excluded.in_stock,
                stock_count = excluded.stock_count,
                image_url = excluded.image_url,
                category = excluded.category,
                upc = COALESCE(excluded.upc, books.upc),
                description = COALESCE(excluded.description, books.description),
                updated_at = excluded.updated_at
        """

        # BookItem 모델 데이터를 파라미터 매핑 리스트로 변환
        params_list = []
        for book in books:
            row_dict = book.model_dump()
            # in_stock 불리언을 정수형(1 또는 0)으로 변환
            row_dict["in_stock"] = 1 if book.in_stock else 0
            # 갱신 시각 추가
            row_dict["updated_at"] = now_str
            params_list.append(row_dict)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 다량의 데이터를 한번에 처리
            cursor.executemany(upsert_query, params_list)
            conn.commit()

        # 처리된 도서 건수 반환
        return len(books)

    def count(self) -> int:
        """DB에 저장된 총 도서 레코드 수를 반환합니다."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM books")
            # 첫 번째 컬럼의 카운트 결과 반환
            return int(cursor.fetchone()[0])

    def get_books_by_category(self, category: Optional[str] = None) -> list[dict]:
        """특정 카테고리(또는 전체)의 도서 목록을 반환합니다."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category:
                # 카테고리 필터링 쿼리 실행
                cursor.execute(
                    "SELECT * FROM books WHERE category = ? ORDER BY id ASC",
                    (category,),
                )
            else:
                # 전체 조회 쿼리 실행
                cursor.execute("SELECT * FROM books ORDER BY id ASC")

            # 행 객체를 일반 딕셔너리로 변환하여 반환
            return [dict(row) for row in cursor.fetchall()]
