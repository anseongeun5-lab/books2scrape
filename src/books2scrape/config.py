"""books2scrape 패키지의 환경설정 및 상수 정의 모듈입니다."""

from pathlib import Path

# 프로젝트 루트 경로 계산 (현재 파일 기준 상위 2단계)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 결과 데이터를 저장할 기본 디렉터리 경로 설정
DATA_DIR = BASE_DIR / "data"

# 스크래핑 대상 웹사이트 기본 URL 설정
BASE_URL = "https://books.toscrape.com/"

# 카탈로그 페이지 기본 URL 포맷 (예: catalogue/page-1.html)
CATALOGUE_PAGE_URL = "https://books.toscrape.com/catalogue/page-{page}.html"

# HTTP 요청 시 사용할 기본 타임아웃 시간(초) 설정
DEFAULT_TIMEOUT = 10.0

# 웹 크롤러 차단 방지용 기본 HTTP 헤더 설정
DEFAULT_HEADERS = {
    # 브라우저 환경을 흉내내는 User-Agent 문자열 지정
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# 웹페이지의 영문 별점 텍스트를 정수 숫자로 변환하는 매핑 딕셔너리
RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}
