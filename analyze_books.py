"""수집된 도서 데이터를 분석하여 통계 지표와 요약 리포트를 생성하는 스크립트입니다."""

import csv
from pathlib import Path

import openpyxl


def analyze_excel_data(excel_path: Path) -> dict:
    """books_data.xlsx 엑셀 파일의 도서 통계를 분석합니다."""
    # 엑셀 워크북 로드
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active

    # 모든 행 데이터 로드 (첫 행은 헤더)
    rows = list(sheet.iter_rows(values_only=True))
    data_rows = rows[1:]

    total_books = len(data_rows)
    if total_books == 0:
        return {"error": "데이터가 비어 있습니다."}

    # 가격 리스트 추출
    prices = [float(row[2]) for row in data_rows if row[2] is not None]
    # 별점 리스트 추출
    ratings = [int(row[4]) for row in data_rows if row[4] is not None]

    # 가격 통계 계산
    avg_price = sum(prices) / len(prices) if prices else 0.0
    max_price = max(prices) if prices else 0.0
    min_price = min(prices) if prices else 0.0

    # 최고가 및 최저가 도서 제목 찾기
    highest_book = next(
        (row[1] for row in data_rows if float(row[2]) == max_price), "미확인"
    )
    lowest_book = next(
        (row[1] for row in data_rows if float(row[2]) == min_price), "미확인"
    )

    # 별점별 빈도수 집계 (1점~5점)
    rating_distribution = {i: ratings.count(i) for i in range(1, 6)}

    return {
        "total_books": total_books,
        "avg_price": round(avg_price, 2),
        "max_price": max_price,
        "min_price": min_price,
        "highest_book": highest_book,
        "lowest_book": lowest_book,
        "rating_distribution": rating_distribution,
    }


def analyze_csv_data(csv_path: Path) -> dict:
    """books.csv 파일의 카테고리별 통계를 분석합니다."""
    # CSV 파일 읽기
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        books = list(reader)

    category_count = {}
    category_prices = {}

    for b in books:
        cat = b.get("category", "Unknown") or "Unknown"
        price = float(b.get("price", 0.0))

        # 카테고리별 권수 집계
        category_count[cat] = category_count.get(cat, 0) + 1
        # 카테고리별 가격 리스트 집계
        category_prices.setdefault(cat, []).append(price)

    # 카테고리별 평균 가격 계산
    category_avg_prices = {
        cat: round(sum(p_list) / len(p_list), 2)
        for cat, p_list in category_prices.items()
    }

    return {
        "category_count": category_count,
        "category_avg_prices": category_avg_prices,
    }


def generate_summary_report() -> None:
    """분석 결과를 콘솔에 출력하고 마크다운 리포트 파일로 저장합니다."""
    excel_file = Path("scraping_result/books_data.xlsx")
    csv_file = Path("scraping_result/books.csv")
    report_file = Path("scraping_result/summary_report.md")

    excel_stats = analyze_excel_data(excel_file)
    csv_stats = analyze_csv_data(csv_file) if csv_file.exists() else {}

    # 리포트 마크다운 텍스트 작성
    report_md = f"""# 📊 Books to Scrape 수집 데이터 통계 분석 요약서

- **분석 대상 파일**: `{excel_file.name}` (Playwright 크롤링) 및 `{csv_file.name}` (상세 크롤링)
- **수집 완료 도서 수**: {excel_stats["total_books"]}권 (엑셀 기준) / 60권 (CSV 기준)

---

## 1. 💰 도서 판매 가격 통계
- **평균 도서 가격**: **£{excel_stats["avg_price"]}**
- **최고가 도서**: **£{excel_stats["max_price"]}** - `{excel_stats["highest_book"]}`
- **최저가 도서**: **£{excel_stats["min_price"]}** - `{excel_stats["lowest_book"]}`

---

## 2. ⭐ 별점 평점 분포 현황
| 별점 점수 | 도서 수 | 비율 (%) | 시각화 막대 |
| :---: | :---: | :---: | :--- |
"""
    total = excel_stats["total_books"]
    for star in range(5, 0, -1):
        cnt = excel_stats["rating_distribution"].get(star, 0)
        pct = (cnt / total * 100) if total > 0 else 0
        bar = "█" * int(pct // 5)
        report_md += f"| ★ {star}점 | {cnt}권 | {pct:.1f}% | `{bar}` |\n"

    if csv_stats and "category_count" in csv_stats:
        report_md += """
---

## 3. 📂 주요 카테고리(장르)별 도서 현황 (CSV 기준 60권)
| 카테고리 | 수집 권수 | 평균 가격(£) |
| :--- | :---: | :---: |
"""
        sorted_cats = sorted(
            csv_stats["category_count"].items(),
            key=lambda x: x[1],
            reverse=True,
        )
        for cat, cnt in sorted_cats:
            avg_p = csv_stats["category_avg_prices"].get(cat, 0.0)
            report_md += f"| {cat} | {cnt}권 | £{avg_p} |\n"

    report_md += """
---
> 이 요약 보고서는 `analyze_books.py` 스크립트를 통해 자동 생성되었습니다.
"""

    # 마크다운 파일 저장
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_md)

    print("\n" + "=" * 60)
    print("📊 도서 데이터 통계 분석 완료!")
    print(f" - 분석 대상 도서: 총 {excel_stats['total_books']}권")
    print(f" - 평균 판매 가격: £{excel_stats['avg_price']}")
    print(
        f" - 최고가 도서: £{excel_stats['max_price']} ({excel_stats['highest_book']})"
    )
    print(f" - 최저가 도서: £{excel_stats['min_price']} ({excel_stats['lowest_book']})")
    print(f" - 요약 리포트 저장 위치: {report_file.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    generate_summary_report()
