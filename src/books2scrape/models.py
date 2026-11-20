"""도서 스크래핑 데이터 모델 정의 모듈입니다."""

from typing import Optional

from pydantic import BaseModel, Field


class BookItem(BaseModel):
    """수집된 단일 도서 정보를 표현하는 데이터 모델 클래스입니다."""

    # 도서 전체 제목
    title: str = Field(description="도서명")
    # 파운드(£) 단위의 도서 판매 가격 (소수점 형태)
    price: float = Field(description="판매 가격 (GBP)")
    # 별점 점수 (1점부터 5점까지 정수형)
    rating: int = Field(default=0, ge=0, le=5, description="별점 (1~5)")
    # 재고 상태 문자열 (예: 'In stock')
    availability: str = Field(default="", description="재고 상태 안내 문자열")
    # 실제 재고 보유 여부 불리언 값
    in_stock: bool = Field(default=True, description="재고 보유 여부")
    # 재고 수량 (상세 페이지에서 확인 가능)
    stock_count: int = Field(default=0, ge=0, description="재고 수량")
    # 도서 상세 페이지 절대 URL
    detail_url: str = Field(description="상세 페이지 URL")
    # 도서 표지 이미지 절대 URL
    image_url: str = Field(default="", description="표지 이미지 URL")
    # 도서 분류 카테고리 (예: 'Poetry', 'Fiction' 등)
    category: str = Field(default="Unknown", description="도서 카테고리")
    # 도서 고유 범용 제품 코드 (UPC)
    upc: Optional[str] = Field(default=None, description="범용 제품 코드 (UPC)")
    # 도서 줄거리 및 세부 설명 요약본
    description: Optional[str] = Field(default="", description="도서 상세 설명")
