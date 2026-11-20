# 📚 Books to Scrape 웹 크롤링 & 데이터 엔지니어링 프로젝트

Astral의 차세대 패키지 관리자 **`uv` (Python 3.12+)** 기반으로 구축된 최신 모던 웹 스크래핑 프로젝트입니다.  
**Playwright**, **BeautifulSoup4**, **Selenium**, **HTTPX**를 활용하여 [Books to Scrape](https://books.toscrape.com/) 사이트의 도서 정보와 표지 이미지를 자동 수집하고 **Excel / CSV / SQLite DB**로 안전하게 관리합니다.

---

## 📂 프로젝트 전체 디렉터리 구조

```text
books2scrape/
├── .venv/                      # uv로 관리되는 Python 3.12 격리 가상환경
├── .vscode/
│   └── settings.json           # VS Code / Antigravity IDE 인터프리터 자동 연동
├── Document/
│   ├── crawling_guide.md       # 📖 [비전공자 맞춤] Playwright 웹 크롤링 입문 가이드
│   └── crawling_prompt.md      # 📝 [AI 코드 생성용] 고품질 웹 크롤링 프롬프트 템플릿
├── books_cover_image/          # 🖼️ 자동 다운로드된 도서 표지 이미지 파일들 (40개+)
├── scraping_result/
│   ├── books_data.xlsx         # 📊 Playwright 수집 결과 엑셀 파일 (별점 숫자 변환)
│   └── books.csv               # 📄 고속 엔진 수집 결과 CSV 파일 (상세 정보 포함)
├── src/
│   └── books2scrape/           # 📦 모듈화된 크롤러 패키지
│       ├── __init__.py         # CLI 명령 진입점 (argparse)
│       ├── config.py           # 기본 URL, 타임아웃, 헤더, 별점 매핑 설정
│       ├── database.py         # SQLite DB (books.db) 저장 및 UPSERT 모듈
│       ├── downloader.py       # 표지 이미지 다운로더 및 파일명 정제 모듈
│       ├── exporter.py         # 엑셀/CSV/JSON 내보내기 유틸리티
│       ├── models.py           # Pydantic 기반 도서 데이터 모델 (BookItem)
│       └── scraper.py          # HTTPX / BS4 / Selenium 하이브리드 스크래퍼
├── tests/
│   ├── __init__.py             # 단위 테스트 패키지 식별
│   ├── test_main.py            # 환경 설정 검증 단위 테스트
│   └── test_scraper.py         # 파싱, DB, 파일 저장 단위 테스트 스위트 (7개)
├── run_crawler.py              # 🚀 [추천] Next 버튼 자동 반복 + 엑셀/이미지 수집기
├── pyproject.toml              # 프로젝트 및 의존성 명세서 (PEP 621 준수)
├── uv.lock                     # 결정론적 의존성 잠금 파일
└── README.md                   # 프로젝트 통합 안내서
```

---

## 🚀 빠른 시작 및 실행 방법

### 1. 가상 환경 동기화
새로운 환경에서 의존성을 단 1초 만에 복원합니다:
```powershell
uv sync
```

### 2. 추천 실행 방식 A: Playwright 자동화 크롤러 실행
> `Next` 버튼을 누르며 도서 정보를 수집하고, `scraping_result/books_data.xlsx`와 `books_cover_image/` 폴더에 분리 저장합니다.
> (웹 트래픽 방지 딜레이, 페이지 변경 후 1초 대기, 에러 발생 시 최대 3회 재시도 내장)
```powershell
uv run python run_crawler.py
```

### 3. 추천 실행 방식 B: 고속 CLI 엔진 실행
> 특정 페이지만 빠르게 긁거나, 특정 카테고리만 골라서 수집하고 싶을 때 사용합니다.
```powershell
# 기본 1페이지(20권) 수집 후 CSV 저장
uv run books2scrape

# 3페이지(60권) 수집 및 상세 설명(UPC, 줄거리)까지 보강하여 JSON 저장
uv run books2scrape --pages 3 --detail --output scraping_result/books.json

# 'Poetry' 카테고리 도서만 골라서 수집
uv run books2scrape --category "Poetry" --output scraping_result/poetry.csv

# 지원되는 전체 50개 카테고리 목록 조회
uv run books2scrape --list-categories

# 표지 이미지 다운로드 및 SQLite DB(books.db) 동시 저장
uv run books2scrape --pages 2 --download-images --save-db
```

---

## 🧪 코드 무결성 검증

프로젝트의 모든 코드는 표준 규격과 단위 테스트를 100% 통과합니다:

```powershell
# 단위 테스트 전체 실행 (pytest)
uv run pytest

# 코드 스타일 및 린트 검사 (Ruff)
uv run ruff check .

# 코드 서식 자동 정렬 (Ruff Format)
uv run ruff format .
```

---

## 📚 제작된 문서 안내

1. **[`Document/crawling_guide.md`](Document/crawling_guide.md)**:
   - 비전공자도 쉽게 이해할 수 있는 크롤링 기초 개념
   - Books to Scrape 사이트에서 파싱 가능한 데이터 12가지 항목 완벽 정리
   - CSS 선택자(Selector) 지도 및 단계별 Playwright 튜토리얼
2. **[`Document/crawling_prompt.md`](Document/crawling_prompt.md)**:
   - 다른 AI 모델(ChatGPT, Claude 등)에게 질문할 때 바로 복사해서 쓸 수 있는 완성형 프롬프트
   - 엑셀 저장, 이미지 분리 다운로드, 별점 숫자 변환, 3회 재시도, 1초 대기 요구사항 반영
