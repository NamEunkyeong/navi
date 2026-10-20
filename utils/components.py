"""
utils/components.py
───────────────────
재사용 가능한 UI 컴포넌트.

KPI 카드, 상단 헤더, Footer 등을 렌더링한다.
HTML 문자열은 textwrap.dedent()를 적용해 Streamlit이
들여쓰기된 HTML을 Markdown 코드 블록으로 해석하지 않도록 한다.
"""

from __future__ import annotations

from collections.abc import Callable
from textwrap import dedent

import pandas as pd
import streamlit as st

from utils.util import MILLION


Translator = Callable[..., str]


# ════════════════════════════════════════════════════════════════
# 헤더 / 상단 배지
# ════════════════════════════════════════════════════════════════
def render_top_header(
    title: str,
    subtitle: str,
    period_label: str,
    currency: str,
) -> None:
    """상단 헤더를 렌더링한다."""
    html = dedent(
        f"""
        <div class="top-header">
            <div class="top-header-left">
                <h1 class="top-header-title">{title}</h1>
                <p class="top-header-subtitle">{subtitle}</p>
            </div>
            <div class="top-header-right">
                <span class="badge badge-period">{period_label}</span>
                <span class="badge badge-currency">{currency}</span>
            </div>
        </div>
        """
    ).strip()

    st.markdown(
        html,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
# KPI 카드
# ════════════════════════════════════════════════════════════════
def _fmt_kpi(
    val: float,
    kind: str,
    currency_symbol: str,
) -> str:
    """KPI 카드 값을 포맷한다."""
    if pd.isna(val):
        return "-"

    if kind == "amount":
        return f"{currency_symbol}{val / MILLION:,.1f}M"

    if kind == "percent":
        return f"{val:.2f}%"

    if kind == "diff_amount":
        return f"{currency_symbol}{val / MILLION:+,.1f}M"

    if kind == "diff_percent":
        return f"{val:+.2f}%p"

    return str(val)


def render_kpi_cards(
    kpis: list[dict],
) -> None:
    """KPI 카드 컬럼을 렌더링한다."""
    if not kpis:
        return

    columns = st.columns(
        len(kpis)
    )

    for column, kpi in zip(
        columns,
        kpis,
    ):
        delta_html = ""

        if kpi.get("delta") is not None:
            delta_class = kpi.get(
                "delta_color",
                "neutral",
            )

            if delta_class == "positive":
                arrow = "▲"
            elif delta_class == "negative":
                arrow = "▼"
            else:
                arrow = "·"

            delta_html = (
                f'<div class="kpi-delta kpi-delta-{delta_class}">'
                f'{arrow} {kpi["delta"]}'
                f"</div>"
            )

        card_html = dedent(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{kpi["label"]}</div>
                <div class="kpi-value">{kpi["value"]}</div>
                {delta_html}
            </div>
            """
        ).strip()

        with column:
            st.markdown(
                card_html,
                unsafe_allow_html=True,
            )


def build_summary_kpis(
    comp_table: pd.DataFrame,
    pg_table: pd.DataFrame,
    currency: str,
    t: Translator | None = None,
) -> list[dict]:
    """
    Summary 탭용 KPI 카드를 생성한다.

    pg_table 인수는 기존 호출부와의 호환성을 위해 유지한다.
    """
    del pg_table

    symbol = (
        "$"
        if currency == "USD"
        else "₩"
    )

    if "TOTAL (Company)" not in comp_table.index:
        return []

    row = comp_table.loc[
        "TOTAL (Company)"
    ]

    anp_current = float(
        row[("CURR", "ANP")]
    )

    anp_difference = float(
        row[("CURR", "ANP")]
        - row[("PREV", "ANP")]
    )

    vnb_current = float(
        row[("CURR", "VNB")]
    )

    vnb_difference = float(
        row[("DIFF", "VNB")]
    )

    margin_current = float(
        row[("CURR", "VNB%")]
    )

    margin_difference = float(
        row[("DIFF", "VNB%")]
    )

    if t is None:
        current_anp_label = "Current Quarter ANP"
        current_vnb_label = "Current Quarter VNB"
        margin_label = "VNB Margin"
        versus_previous = "vs Prev"
    else:
        current_anp_label = t(
            "current_quarter_anp"
        )

        current_vnb_label = t(
            "current_quarter_vnb"
        )

        margin_label = t(
            "vnb_margin"
        )

        versus_previous = t(
            "vs_previous"
        )

    return [
        {
            "label": current_anp_label,
            "value": _fmt_kpi(
                anp_current,
                "amount",
                symbol,
            ),
            "delta": (
                f"{_fmt_kpi(anp_difference, 'diff_amount', symbol)} "
                f"{versus_previous}"
            ),
            "delta_color": (
                "positive"
                if anp_difference > 0
                else (
                    "negative"
                    if anp_difference < 0
                    else "neutral"
                )
            ),
        },
        {
            "label": current_vnb_label,
            "value": _fmt_kpi(
                vnb_current,
                "amount",
                symbol,
            ),
            "delta": (
                f"{_fmt_kpi(vnb_difference, 'diff_amount', symbol)} "
                f"{versus_previous}"
            ),
            "delta_color": (
                "positive"
                if vnb_difference > 0
                else (
                    "negative"
                    if vnb_difference < 0
                    else "neutral"
                )
            ),
        },
        {
            "label": margin_label,
            "value": _fmt_kpi(
                margin_current,
                "percent",
                symbol,
            ),
            "delta": (
                f"{_fmt_kpi(margin_difference, 'diff_percent', symbol)} "
                f"{versus_previous}"
            ),
            "delta_color": (
                "positive"
                if margin_difference > 0
                else (
                    "negative"
                    if margin_difference < 0
                    else "neutral"
                )
            ),
        },
    ]


# ════════════════════════════════════════════════════════════════
# Footer
# ════════════════════════════════════════════════════════════════
def render_footer(
    t: Translator | None = None,
) -> None:
    """대시보드 Footer를 렌더링한다."""
    if t is None:
        dashboard_label = "VNB Walk Analysis Dashboard"
        powered_by_label = "Powered by Actuarial Analytics"
    else:
        dashboard_label = t(
            "footer_dashboard"
        )

        powered_by_label = t(
            "footer_powered_by"
        )

    footer_html = dedent(
        f"""
        <div class="footer">
            <span>{dashboard_label}</span>
            <span class="footer-sep">·</span>
            <span>{powered_by_label}</span>
        </div>
        """
    ).strip()

    st.markdown(
        footer_html,
        unsafe_allow_html=True,
    )