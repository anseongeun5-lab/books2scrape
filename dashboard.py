"""Books to Scrape 수집 데이터를 위한 Streamlit 및 Plotly 기반 인터랙티브 대시보드입니다.

[핵심 기능]
1. 사이드바 필터: 별점(1~5점), 가격 범위 슬라이더, 도서명 검색, 재고 상태 필터
2. Plotly 인터랙티브 시각화: 마우스 호버(Hover) 시 도서 표지 이미지, 제목, 가격, 별점 툴팁 노출
3. 도서 카드 갤러리: 실제 로컬 표지 이미지와 함께 5가지 정보(제목, 가격, 재고, 별점, 링크) 카드 렌더링
4. 데이터 테이블 뷰 및 엑셀 다운로드 지원
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Streamlit 웹페이지 레이아웃 및 브라우저 탭 타이틀 설정
st.set_page_config(
    page_title="Books to Scrape 도서 데이터 대시보드",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_book_dataset() -> pd.DataFrame:
    """엑셀 파일(books_data.xlsx)에서 도서 데이터를 읽어와 판다스 DataFrame으로 반환합니다."""
    # 엑셀 파일 경로 지정
    excel_path = Path("scraping_result/books_data.xlsx")

    if not excel_path.exists():
        # 파일이 없을 경우 빈 데이터프레임 반환
        st.error(f"데이터 파일을 찾을 수 없습니다: {excel_path.resolve()}")
        return pd.DataFrame()

    # pandas를 이용해 엑셀 파일 로드
    df = pd.read_excel(excel_path)

    # 가격 컬럼 숫자형으로 보장
    df["가격(£)"] = pd.to_numeric(df["가격(£)"], errors="coerce")
    # 별점 컬럼 정수형으로 보장
    df["별점(숫자)"] = (
        pd.to_numeric(df["별점(숫자)"], errors="coerce").fillna(0).astype(int)
    )

    # 별점 시각용 별표 문자열 컬럼 생성 (예: ★★★☆☆)
    df["별점(아이콘)"] = df["별점(숫자)"].apply(
        lambda r: "★" * int(r) + "☆" * (5 - int(r))
    )

    # 로컬 이미지 파일 존재 여부 확인 및 경로 매핑
    def resolve_image_path(row_path: str) -> str:
        p = Path(row_path)
        return str(p) if p.exists() else ""

    df["유효로컬이미지"] = df["저장된이미지경로"].apply(resolve_image_path)

    return df


def main() -> None:
    """대시보드 메인 레이아웃 및 인터랙티브 위젯을 구성합니다."""
    # 상단 대시보드 헤더
    st.title("📚 Books to Scrape 인터랙티브 도서 대시보드")
    st.markdown(
        "수집된 **도서 제목, 가격, 재고 상태, 별점, 표지 이미지** 데이터를 인터랙티브하게 탐색하고 시각화합니다."
    )
    st.markdown("---")

    # 도서 데이터셋 로드
    df = load_book_dataset()
    if df.empty:
        st.warning(
            "표시할 데이터가 없습니다. 먼저 `uv run python main_crawler.py`를 실행해 주세요."
        )
        return

    # =========================================================
    # 1. 사이드바 인터랙티브 필터 컨트롤러
    # =========================================================
    st.sidebar.header("🔍 도서 필터 옵션")

    # 1-1. 검색어 필터 (도서 제목 실시간 검색)
    search_query = st.sidebar.text_input(
        "도서 제목 검색", placeholder="예: Light, Velvet..."
    )

    # 1-2. 가격 범위 슬라이더 필터
    min_price_val = float(df["가격(£)"].min())
    max_price_val = float(df["가격(£)"].max())
    price_range = st.sidebar.slider(
        "가격 범위 선택 (£)",
        min_value=min_price_val,
        max_value=max_price_val,
        value=(min_price_val, max_price_val),
        step=0.5,
    )

    # 1-3. 별점 멀티 선택 필터 (1~5점)
    all_ratings = sorted(df["별점(숫자)"].unique().tolist())
    selected_ratings = st.sidebar.multiselect(
        "별점 선택",
        options=all_ratings,
        default=all_ratings,
        format_func=lambda x: f"★ {x}점 ({'★' * x})",
    )

    # 1-4. 재고 상태 필터
    stock_options = ["전체"] + sorted(df["재고상태"].dropna().unique().tolist())
    selected_stock = st.sidebar.selectbox("재고 상태", options=stock_options)

    # =========================================================
    # 2. 필터링 로직 적용
    # =========================================================
    filtered_df = df.copy()

    # 제목 검색 필터링
    if search_query:
        filtered_df = filtered_df[
            filtered_df["도서제목"].str.contains(search_query, case=False, na=False)
        ]

    # 가격 범위 필터링
    filtered_df = filtered_df[
        (filtered_df["가격(£)"] >= price_range[0])
        & (filtered_df["가격(£)"] <= price_range[1])
    ]

    # 별점 필터링
    if selected_ratings:
        filtered_df = filtered_df[filtered_df["별점(숫자)"].isin(selected_ratings)]

    # 재고 상태 필터링
    if selected_stock != "전체":
        filtered_df = filtered_df[filtered_df["재고상태"] == selected_stock]

    # =========================================================
    # 3. 핵심 통계 지표 (KPI Metrics) 카드
    # =========================================================
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="조회 도서 수",
            value=f"{len(filtered_df)}권",
            delta=f"전체 {len(df)}권 중",
        )
    with col2:
        avg_price = filtered_df["가격(£)"].mean() if not filtered_df.empty else 0.0
        st.metric(label="평균 판매 가격", value=f"£{avg_price:.2f}")
    with col3:
        avg_rating = filtered_df["별점(숫자)"].mean() if not filtered_df.empty else 0.0
        st.metric(label="평균 별점 점수", value=f"★ {avg_rating:.1f} / 5.0")
    with col4:
        min_p = filtered_df["가격(£)"].min() if not filtered_df.empty else 0.0
        max_p = filtered_df["가격(£)"].max() if not filtered_df.empty else 0.0
        st.metric(label="가격대 범위", value=f"£{min_p:.1f} ~ £{max_p:.1f}")

    st.markdown("---")

    # =========================================================
    # 4. Plotly 인터랙티브 산점도 & 호버 툴팁 시각화
    # =========================================================
    st.subheader("📈 [Plotly 시각화] 가격 vs 별점 인터랙티브 산점도")
    st.caption(
        "💡 차트의 각 점에 **마우스를 올려놓으면(Hover)** 도서 제목, 가격, 별점 및 표지 이미지 링크가 툴팁으로 표시됩니다."
    )

    if not filtered_df.empty:
        # Plotly 산점도 차트 생성
        fig = px.scatter(
            filtered_df,
            x="가격(£)",
            y="별점(숫자)",
            size="가격(£)",
            color="별점(숫자)",
            color_continuous_scale="Viridis",
            hover_name="도서제목",
            custom_data=[
                "도서제목",
                "가격(£)",
                "별점(아이콘)",
                "재고상태",
                "이미지URL",
                "상세페이지링크",
            ],
            labels={
                "가격(£)": "판매 가격 (GBP £)",
                "별점(숫자)": "별점 점수 (1~5)",
            },
            title="도서 가격 및 별점 분포도 (점 크기: 가격 비례)",
            height=500,
        )

        # 툴팁(Hover) 템플릿 커스터마이징 (제목, 가격, 별점, 재고, 이미지 링크 안내)
        fig.update_traces(
            hovertemplate="<br>".join(
                [
                    "<b>📖 도서명: %{customdata[0]}</b>",
                    "💰 가격: £%{customdata[1]:.2f}",
                    "⭐ 평점: %{customdata[2]}",
                    "📦 재고: %{customdata[3]}",
                    "🖼️ 표지 이미지: %{customdata[4]}",
                    "<extra></extra>",  # 불필요한 보조 정보 숨김
                ]
            )
        )

        # y축 별점 1~5 정수 눈금 고정
        fig.update_layout(
            yaxis=dict(tickmode="linear", tick0=1, dtick=1, range=[0.5, 5.5]),
            margin=dict(l=40, r=40, t=50, b=40),
        )

        # Streamlit에 Plotly 차트 렌더링
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("선택된 필터 조건에 부합하는 도서가 없습니다.")

    st.markdown("---")

    # =========================================================
    # 5. 도서 표지 이미지 & 세부 정보 카드 갤러리
    # =========================================================
    st.subheader("🖼️ 도서 카드 갤러리 뷰")
    st.caption("필터링된 각 도서의 실제 표지 이미지와 5가지 핵심 정보 카드입니다.")

    if not filtered_df.empty:
        # 한 줄에 4개씩 카드 배치
        cols_per_row = 4
        books_list = filtered_df.to_dict(orient="records")

        for i in range(0, len(books_list), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(books_list):
                    book = books_list[idx]
                    with col:
                        # 1. 표지 이미지 렌더링 (로컬 파일 우선, 없으면 원본 URL)
                        local_img = book.get("유효로컬이미지")
                        img_source = (
                            local_img
                            if local_img and Path(local_img).exists()
                            else book.get("이미지URL")
                        )

                        try:
                            st.image(
                                img_source,
                                use_container_width=True,
                                caption=f"No. {book['순번']}",
                            )
                        except Exception:
                            st.write("🖼️ [이미지 로딩 불가]")

                        # 2. 도서 제목 (길면 줄바꿈)
                        st.markdown(f"**{book['도서제목']}**")

                        # 3. 가격 & 별점
                        st.markdown(
                            f"**가격**: `£{book['가격(£)']:.2f}` &nbsp;|&nbsp; **별점**: {book['별점(아이콘)']}"
                        )

                        # 4. 재고 상태
                        st.caption(f"📦 {book['재고상태']}")

                        # 5. 상세 페이지 링크 버튼
                        st.link_button(
                            "상세보기 ↗",
                            book["상세페이지링크"],
                            use_container_width=True,
                        )
                        st.write("")
    else:
        st.info("표시할 도서가 없습니다.")

    st.markdown("---")

    # =========================================================
    # 6. 원본 데이터 테이블 및 다운로드
    # =========================================================
    with st.expander("📋 필터링된 전체 도서 데이터 테이블 보기"):
        st.dataframe(
            filtered_df[
                [
                    "순번",
                    "도서제목",
                    "가격(£)",
                    "별점(숫자)",
                    "재고상태",
                    "상세페이지링크",
                    "이미지URL",
                ]
            ],
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
