"""
utils/auto_analysis/_common.py
──────────────────────────────
자동 분석 초안 생성 공통 헬퍼.

금액, 퍼센트 및 증감 방향을 언어 설정에 맞게 포맷한다.
"""

from __future__ import annotations

import pandas as pd

from utils.util import MILLION


def _is_english(
    language: str | None,
) -> bool:
    """언어 값이 English인지 확인한다."""
    return str(language).strip().lower() in {
        "english",
        "en",
        "eng",
    }


def _fmt_amt(
    val: float,
    display_currency: str = "KRW",
) -> str:
    """금액을 Millions 단위 문자열로 변환한다."""
    if pd.isna(val):
        return "-"

    symbol = (
        "$"
        if display_currency == "USD"
        else "₩"
    )

    return (
        f"{symbol}"
        f"{val / MILLION:,.1f}M"
    )


def _fmt_pct(
    val: float,
    with_sign: bool = False,
    suffix: str = "%",
) -> str:
    """퍼센트 또는 Percentage Point 문자열을 생성한다."""
    if pd.isna(val):
        return "-"

    number_format = (
        "+,.2f"
        if with_sign
        else ",.2f"
    )

    return f"{val:{number_format}}{suffix}"


def _trend_word(
    diff: float,
    positive_word: str | None = None,
    negative_word: str | None = None,
    *,
    language: str = "Korean",
    neutral_word: str | None = None,
) -> str:
    """
    증감 방향에 따른 문구를 반환한다.

    Parameters
    ----------
    diff:
        증감 값.

    positive_word:
        양수일 때 사용할 사용자 지정 문구.

    negative_word:
        음수일 때 사용할 사용자 지정 문구.

    language:
        Korean 또는 English.

    neutral_word:
        0일 때 사용할 사용자 지정 문구.

    Notes
    -----
    기존 호출 방식과 호환된다.

    예시:
        _trend_word(diff)
        _trend_word(diff, "초과", "미달")
        _trend_word(
            diff,
            "above",
            "below",
            language="English",
        )
    """
    is_english = _is_english(language)

    if positive_word is None:
        positive_word = (
            "increase"
            if is_english
            else "증가"
        )

    if negative_word is None:
        negative_word = (
            "decrease"
            if is_english
            else "감소"
        )

    if neutral_word is None:
        neutral_word = (
            "unchanged"
            if is_english
            else "보합"
        )

    if diff > 0:
        return positive_word

    if diff < 0:
        return negative_word

    return neutral_word


def _direction_label(
    diff: float,
    *,
    language: str = "Korean",
) -> str:
    """증감 방향을 문장용 명사 형태로 반환한다."""
    if _is_english(language):
        if diff > 0:
            return "increase"

        if diff < 0:
            return "decrease"

        return "no change"

    if diff > 0:
        return "증가"

    if diff < 0:
        return "감소"

    return "변동 없음"


def _positive_negative_label(
    value: float,
    *,
    language: str = "Korean",
) -> str:
    """값의 부호를 Positive / Negative 문구로 반환한다."""
    if value > 0:
        return (
            "Positive"
            if _is_english(language)
            else "Positive"
        )

    if value < 0:
        return (
            "Negative"
            if _is_english(language)
            else "Negative"
        )

    return (
        "Neutral"
        if _is_english(language)
        else "Neutral"
    )