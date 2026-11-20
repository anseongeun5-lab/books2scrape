"""수집된 도서 데이터를 바탕으로 단독 실행 가능한 인터랙티브 HTML 대시보드를 생성하는 스크립트입니다.

[특징]
- 서버 구동 없이도 브라우저에서 바로 열 수 있는 standalone HTML 파일 생성
- 마우스 호버(Hover) 시 실제 도서 표지 이미지와 5가지 정보(제목, 가격, 별점, 재고)가 툴팁으로 표시
- 실시간 가격 슬라이더, 별점 필터, 도서명 검색 기능 내장
"""

import json
from pathlib import Path

import openpyxl


def build_standalone_dashboard_html() -> Path:
    """books_data.xlsx 파일로부터 데이터를 읽어 standalone 인터랙티브 HTML 대시보드를 생성합니다."""
    # 엑셀 파일 로드
    excel_path = Path("scraping_result/books_data.xlsx")
    output_html_path = Path("scraping_result/interactive_dashboard.html")

    if not excel_path.exists():
        raise FileNotFoundError(f"엑셀 파일을 찾을 수 없습니다: {excel_path.resolve()}")

    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active
    rows = list(sheet.iter_rows(values_only=True))

    data_rows = rows[1:]

    # 자바스크립트에서 활용할 수 있도록 도서 목록 딕셔너리 리스트 생성
    books_data = []
    for r in data_rows:
        books_data.append(
            {
                "id": r[0],
                "title": r[1],
                "price": float(r[2]) if r[2] is not None else 0.0,
                "availability": r[3] or "",
                "rating": int(r[4]) if r[4] is not None else 0,
                "detail_url": r[5] or "",
                "image_url": r[6] or "",
                "local_image": r[7] or "",
            }
        )

    # JSON 문자열로 직렬화
    books_json = json.dumps(books_data, ensure_ascii=False)

    # HTML 템플릿 작성 (모던 CSS + JavaScript 인터랙션 + Hover 툴팁 + 필터)
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>Books to Scrape 인터랙티브 대시보드</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- Chart.js 및 Plotly CDN 로드 -->
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {{
      --primary: #4361ee;
      --primary-light: #eef2ff;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text: #1e293b;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --star: #f59e0b;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }}
    .header {{
      background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
      color: white;
      padding: 24px 32px;
      border-radius: 16px;
      margin-bottom: 24px;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }}
    .header h1 {{ font-size: 26px; margin-bottom: 8px; font-weight: 700; }}
    .header p {{ color: #94a3b8; font-size: 14px; }}
    
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .stat-card {{
      background: var(--card-bg);
      padding: 20px;
      border-radius: 12px;
      border: 1px solid var(--border);
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .stat-label {{ font-size: 13px; color: var(--text-muted); margin-bottom: 6px; font-weight: 600; text-transform: uppercase; }}
    .stat-value {{ font-size: 26px; font-weight: 700; color: var(--primary); }}

    .main-layout {{
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 24px;
    }}
    @media (max-width: 900px) {{
      .main-layout {{ grid-template-columns: 1fr; }}
    }}

    .filter-panel {{
      background: var(--card-bg);
      padding: 24px;
      border-radius: 12px;
      border: 1px solid var(--border);
      height: fit-content;
      position: sticky;
      top: 24px;
    }}
    .filter-group {{ margin-bottom: 20px; }}
    .filter-label {{ font-size: 14px; font-weight: 600; margin-bottom: 8px; display: block; }}
    input[type="text"] {{
      width: 100%;
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 14px;
      outline: none;
    }}
    input[type="range"] {{ width: 100%; }}
    .rating-buttons {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .btn-rating {{
      padding: 6px 12px;
      border: 1px solid var(--border);
      background: white;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      transition: all 0.2s;
    }}
    .btn-rating.active {{
      background: var(--primary);
      color: white;
      border-color: var(--primary);
    }}

    .chart-container {{
      background: var(--card-bg);
      padding: 20px;
      border-radius: 12px;
      border: 1px solid var(--border);
      margin-bottom: 24px;
    }}

    .gallery-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
      gap: 16px;
    }}
    .book-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      position: relative;
      transition: transform 0.2s, box-shadow 0.2s;
    }}
    .book-card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }}
    .card-img-wrapper {{
      width: 100%;
      height: 220px;
      background: #f1f5f9;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }}
    .card-img {{
      width: 100%;
      height: 100%;
      object-fit: cover;
    }}
    .card-body {{ padding: 14px; display: flex; flex-direction: column; flex: 1; }}
    .book-title {{
      font-size: 14px;
      font-weight: 600;
      line-height: 1.4;
      margin-bottom: 8px;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .book-meta {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: auto;
      padding-top: 8px;
    }}
    .book-price {{ font-size: 16px; font-weight: 700; color: #0f172a; }}
    .book-stars {{ color: var(--star); font-size: 13px; }}
    .book-stock {{ font-size: 11px; color: #16a34a; font-weight: 600; margin-top: 4px; }}
    .btn-detail {{
      margin-top: 10px;
      padding: 6px 10px;
      background: var(--primary-light);
      color: var(--primary);
      text-align: center;
      border-radius: 6px;
      text-decoration: none;
      font-size: 12px;
      font-weight: 600;
      transition: background 0.2s;
    }}
    .btn-detail:hover {{ background: #dbeafe; }}
  </style>
</head>
<body>

  <div class="header">
    <h1>📚 Books to Scrape 인터랙티브 대시보드</h1>
    <p>도서명, 가격, 재고상태, 별점 및 표지 이미지 데이터를 탐색하고 필터링하는 대시보드입니다.</p>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-label">조회 도서 수</div>
      <div class="stat-value" id="kpi-count">0권</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">평균 도서 가격</div>
      <div class="stat-value" id="kpi-avg-price">£0.00</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">평균 별점 평점</div>
      <div class="stat-value" id="kpi-avg-rating">★ 0.0</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">가격 범위</div>
      <div class="stat-value" id="kpi-price-range">£0 ~ £0</div>
    </div>
  </div>

  <div class="main-layout">
    <!-- 사이드바 필터 -->
    <div class="filter-panel">
      <h3 style="margin-bottom: 16px; font-size: 16px;">🔍 필터 컨트롤러</h3>
      
      <div class="filter-group">
        <label class="filter-label">도서 제목 검색</label>
        <input type="text" id="search-input" placeholder="제목 검색...">
      </div>

      <div class="filter-group">
        <label class="filter-label">최대 가격 (£): <span id="price-val" style="color:var(--primary); font-weight:700;">전체</span></label>
        <input type="range" id="price-slider" min="10" max="60" step="1" value="60">
      </div>

      <div class="filter-group">
        <label class="filter-label">별점 필터</label>
        <div class="rating-buttons">
          <button class="btn-rating active" data-rating="all">전체</button>
          <button class="btn-rating" data-rating="5">★ 5점</button>
          <button class="btn-rating" data-rating="4">★ 4점</button>
          <button class="btn-rating" data-rating="3">★ 3점</button>
          <button class="btn-rating" data-rating="2">★ 2점</button>
          <button class="btn-rating" data-rating="1">★ 1점</button>
        </div>
      </div>
    </div>

    <!-- 메인 콘텐츠 영역 -->
    <div>
      <!-- Plotly 산점도 차트 -->
      <div class="chart-container">
        <h3 style="font-size: 16px; margin-bottom: 8px;">📈 [Plotly 시각화] 가격 vs 별점 분포 (마우스 호버 시 툴팁 지원)</h3>
        <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">마우스를 점 위에 올리면 도서명, 가격, 별점 및 표지 링크 정보가 나타납니다.</p>
        <div id="plotly-scatter" style="width:100%; height:400px;"></div>
      </div>

      <!-- 갤러리 뷰 -->
      <h3 style="font-size: 18px; margin-bottom: 16px;">🖼️ 도서 카드 갤러리</h3>
      <div class="gallery-grid" id="gallery-container"></div>
    </div>
  </div>

  <script>
    // 파이썬에서 주입된 도서 데이터셋
    const ALL_BOOKS = {books_json};
    let currentRatingFilter = 'all';

    function renderStarIcons(rating) {{
      return '★'.repeat(rating) + '☆'.repeat(5 - rating);
    }}

    function applyFilters() {{
      const query = document.getElementById('search-input').value.toLowerCase().trim();
      const maxPrice = parseFloat(document.getElementById('price-slider').value);

      const filtered = ALL_BOOKS.filter(book => {{
        const matchTitle = book.title.toLowerCase().includes(query);
        const matchPrice = book.price <= maxPrice;
        const matchRating = currentRatingFilter === 'all' || book.rating === parseInt(currentRatingFilter);
        return matchTitle && matchPrice && matchRating;
      }});

      updateKPIs(filtered);
      renderPlotlyChart(filtered);
      renderGallery(filtered);
    }}

    function updateKPIs(books) {{
      document.getElementById('kpi-count').innerText = books.length + '권';
      if (books.length === 0) {{
        document.getElementById('kpi-avg-price').innerText = '£0.00';
        document.getElementById('kpi-avg-rating').innerText = '★ 0.0';
        document.getElementById('kpi-price-range').innerText = '0';
        return;
      }}
      const prices = books.map(b => b.price);
      const ratings = books.map(b => b.rating);
      const avgPrice = prices.reduce((a, b) => a + b, 0) / books.length;
      const avgRating = ratings.reduce((a, b) => a + b, 0) / books.length;

      document.getElementById('kpi-avg-price').innerText = '£' + avgPrice.toFixed(2);
      document.getElementById('kpi-avg-rating').innerText = '★ ' + avgRating.toFixed(1) + ' / 5.0';
      document.getElementById('kpi-price-range').innerText = '£' + Math.min(...prices).toFixed(1) + ' ~ £' + Math.max(...prices).toFixed(1);
    }}

    function renderPlotlyChart(books) {{
      const xVals = books.map(b => b.price);
      const yVals = books.map(b => b.rating);
      const textVals = books.map(b => b.title);
      const hoverTexts = books.map(b => 
        `<b>📖 ${{b.title}}</b><br>💰 가격: £${{b.price.toFixed(2)}}<br>⭐ 평점: ${{renderStarIcons(b.rating)}}<br>📦 재고: ${{b.availability}}<br>🔗 <a href="${{b.detail_url}}" target="_blank">상세페이지 열기</a>`
      );

      const trace = {{
        x: xVals,
        y: yVals,
        text: hoverTexts,
        mode: 'markers',
        marker: {{
          size: xVals.map(p => Math.max(12, p * 0.4)),
          color: yVals,
          colorscale: 'Viridis',
          showscale: true,
          colorbar: {{ title: '별점' }}
        }},
        hovertemplate: '%{{text}}<extra></extra>'
      }};

      const layout = {{
        title: '도서 가격 및 별점 분포',
        xaxis: {{ title: '도서 가격 (GBP £)' }},
        yaxis: {{ title: '별점 점수 (1~5)', dtick: 1, range: [0.5, 5.5] }},
        margin: {{ l: 50, r: 40, t: 40, b: 50 }}
      }};

      Plotly.newPlot('plotly-scatter', [trace], layout, {{ responsive: true }});
    }}

    function renderGallery(books) {{
      const container = document.getElementById('gallery-container');
      container.innerHTML = '';

      if (books.length === 0) {{
        container.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 40px; color:#64748b;">조건에 일치하는 도서가 없습니다.</div>';
        return;
      }}

      books.forEach(b => {{
        const card = document.createElement('div');
        card.className = 'book-card';
        card.innerHTML = `
          <div class="card-img-wrapper">
            <img src="${{b.image_url}}" class="card-img" alt="${{b.title}}" onerror="this.onerror=null; this.src='https://via.placeholder.com/200x260?text=No+Cover';">
          </div>
          <div class="card-body">
            <div class="book-title" title="${{b.title}}">${{b.title}}</div>
            <div class="book-meta">
              <span class="book-price">£${{b.price.toFixed(2)}}</span>
              <span class="book-stars">${{renderStarIcons(b.rating)}}</span>
            </div>
            <div class="book-stock">📦 ${{b.availability}}</div>
            <a href="${{b.detail_url}}" target="_blank" class="btn-detail">상세보기 ↗</a>
          </div>
        `;
        container.appendChild(card);
      }});
    }}

    // 이벤트 리스너 등록
    document.getElementById('search-input').addEventListener('input', applyFilters);
    document.getElementById('price-slider').addEventListener('input', (e) => {{
      document.getElementById('price-val').innerText = '£' + e.target.value;
      applyFilters();
    }});

    document.querySelectorAll('.btn-rating').forEach(btn => {{
      btn.addEventListener('click', (e) => {{
        document.querySelectorAll('.btn-rating').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        currentRatingFilter = e.target.getAttribute('data-rating');
        applyFilters();
      }});
    }});

    // 초기 렌더링
    applyFilters();
  </script>
</body>
</html>
"""

    # HTML 파일 디스크에 쓰기 (UTF-8 인코딩)
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(
        f"[+] 독립형 인터랙티브 HTML 대시보드 생성 완료: {output_html_path.resolve()}"
    )
    return output_html_path


if __name__ == "__main__":
    build_standalone_dashboard_html()
