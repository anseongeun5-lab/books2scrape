"""books2scrape 기본 동작 검증을 위한 단위 테스트 모듈입니다."""

# 테스트 대상 모듈에서 get_greeting 함수 임포트
from books2scrape import get_greeting


def test_get_greeting() -> None:
    """get_greeting 함수가 예상 메시지를 정상 반환하는지 검증합니다."""
    # 안내 메시지 함수 실행 결과 획득
    result = get_greeting()
    # 반환 문자열이 빈 값이 아니며 의도한 문구를 포함하는지 검증
    assert "Books to Scrape" in result
