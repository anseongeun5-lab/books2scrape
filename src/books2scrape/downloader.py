"""도서 표지 이미지 파일 다운로드를 담당하는 모듈입니다."""

import re
from pathlib import Path
from typing import Sequence

import httpx

from books2scrape.config import DEFAULT_HEADERS, DEFAULT_TIMEOUT
from books2scrape.models import BookItem


def sanitize_filename(name: str) -> str:
    """운영체제 파일명으로 사용 불가능한 특수문자를 제거하고 안전한 문자열로 변환합니다."""
    # 공백이나 특수기호를 밑줄(_)로 치환
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    # 연속된 공백 및 언더스코어 정리 후 좌우 공백 제거
    cleaned = re.sub(r"\s+", "_", cleaned).strip("_. ")
    # 빈 문자열 방지용 기본 이름 제공
    return cleaned if cleaned else "unnamed_image"


def download_book_images(
    books: Sequence[BookItem],
    output_dir: Path,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[Path]:
    """도서 목록의 표지 이미지를 로컬 디렉터리에 다운로드하고 저장된 파일 경로 리스트를 반환합니다."""
    # 대상 디렉터리가 없을 경우 자동 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []

    # HTTP 세션 클라이언트 생성
    with httpx.Client(
        headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True
    ) as client:
        for idx, book in enumerate(books, start=1):
            # 이미지 URL이 없으면 다음 도서로 건너뜀
            if not book.image_url:
                continue

            try:
                # 안전한 파일명 생성 (예: 001_A_Light_in_the_Attic.jpg)
                safe_title = sanitize_filename(book.title)[:50]
                # 파일 확장자 추출 (기본값 .jpg)
                ext = Path(book.image_url).suffix or ".jpg"
                filename = f"{idx:03d}_{safe_title}{ext}"
                target_file = output_dir / filename

                # 이미 파일이 존재할 경우 중복 다운로드 방지
                if target_file.exists():
                    saved_paths.append(target_file)
                    continue

                # 이미지 바이너리 다운로드 요청
                response = client.get(book.image_url)
                # HTTP 응답 코드 검증
                response.raise_for_status()

                # 파일 쓰기 (바이너리 모드)
                with target_file.open("wb") as f:
                    f.write(response.content)

                # 성공적으로 저장된 경로 등록
                saved_paths.append(target_file)
                print(f"[다운로드 완료] {filename}")
            except Exception as err:
                # 다운로드 실패 시 경고 출력 후 계속 진행
                print(f"[경고] '{book.title}' 이미지 다운로드 실패: {err}")

    # 저장된 모든 이미지 파일 경로 반환
    return saved_paths
