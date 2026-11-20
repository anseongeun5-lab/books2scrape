"""스크래핑한 도서 데이터를 CSV 및 JSON 파일로 내보내는 모듈입니다."""

import csv
import json
from pathlib import Path
from typing import Sequence

from books2scrape.models import BookItem


def save_to_json(books: Sequence[BookItem], filepath: Path) -> Path:
    """도서 목록을 JSON 포맷 파일로 저장합니다."""
    # 상위 디렉터리가 없을 경우 자동 생성
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # BookItem 모델 리스트를 파이썬 기본 딕셔너리 리스트로 직렬화
    data = [book.model_dump() for book in books]

    # JSON 파일 쓰기 모드로 오픈 (UTF-8 인코딩)
    with filepath.open("w", encoding="utf-8") as f:
        # 가독성을 위해 indent=2 및 한글/특수문자 유지를 위한 ensure_ascii=False 설정
        json.dump(data, f, indent=2, ensure_ascii=False)

    # 저장된 파일 경로 반환
    return filepath


def save_to_csv(books: Sequence[BookItem], filepath: Path) -> Path:
    """도서 목록을 CSV 포맷 파일로 저장합니다."""
    # 상위 디렉터리가 없을 경우 자동 생성
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # 데이터가 비어 있을 경우 빈 파일 생성 후 반환
    if not books:
        filepath.touch(exist_ok=True)
        return filepath

    # 첫 번째 아이템을 기준으로 CSV 헤더 컬럼 목록 획득
    fieldnames = list(books[0].model_dump().keys())

    # CSV 파일 쓰기 모드로 오픈 (엑셀 호환을 위한 utf-8-sig 인코딩)
    with filepath.open("w", encoding="utf-8-sig", newline="") as f:
        # DictWriter 객체 초기화
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # CSV 헤더 라인 작성
        writer.writeheader()
        # 모든 도서 데이터를 한 줄씩 기록
        for book in books:
            writer.writerow(book.model_dump())

    # 저장된 파일 경로 반환
    return filepath


def export_books(books: Sequence[BookItem], output_path: str | Path) -> Path:
    """파일 확장자(.csv 또는 .json)에 따라 적절한 포맷으로 도서 데이터를 자동 내보냅니다."""
    path = Path(output_path)
    # 파일 확장자 소문자로 추출
    suffix = path.suffix.lower()

    if suffix == ".json":
        # JSON 포맷으로 저장
        return save_to_json(books, path)
    # 기본값 또는 .csv인 경우 CSV 포맷으로 저장
    return save_to_csv(books, path)
