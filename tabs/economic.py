"""
tabs/economic.py
────────────────
Economic 탭.

기능
----
- 금리 시나리오 비교
- FA Spread 분석
- FX Rate 비교
- Korean / English UI
- 오프라인 HTML Export
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from styles.theme import (
    C_DEEP_BLUE,
    C_WHITE,
    PRIMARY,
    SUPPORT,
)
from utils.io import load_generic_table
from utils.processor import load_fa_spread
from utils.util import safe_fillna


def render(ctx) -> None:
    """Economic 탭을 렌더링한다."""
    # ── 언어 및 HTML Export ───────────────────────────────────
    language = ctx.language
    t = ctx.t
    html_report = ctx.html_report

    # ── Context ───────────────────────────────────────────────
    cfg = ctx.cfg
    paths = ctx.paths
    quarter = ctx.quarter

    previous_fx_rate = ctx.PREV_FX_RATE
    current_fx_rate = ctx.CURR_FX_RATE

    html_report.add_tab(
        t("tab_economic")
    )

    # ════════════════════════════════════════════════════════════
    # 1. Interest Rate Scenario
    # ════════════════════════════════════════════════════════════
    col_economic_filter, col_economic_chart = st.columns(
        [1, 3]
    )

    with col_economic_filter:
        economic_currency = st.selectbox(
            t("scenario_currency"),
            [
                "KRW",
                "USD",
            ],
            key="economic_scenario_currency",
        )

        st.caption(
            t("economic_scenario_caption")
        )

    with col_economic_chart:
        column_map = {
            "KRW": "TL_GA_KRW",
            "USD": "TL_GA_USD",
        }

        scenario_column = column_map.get(
            economic_currency,
            "TL_GA_KRW",
        )

        period_text = str(quarter)

        def load_fac(
            file_path: str,
            column_name: str,
        ):
            """FAC 파일에서 지정 금리 열을 로드한다."""
            path = Path(file_path)

            if not path.exists():
                return None

            try:
                dataframe = load_generic_table(
                    file_path
                )

                if column_name in dataframe.columns:
                    return (
                        dataframe[
                            column_name
                        ]
                        .astype(float)
                        .values
                        * 100
                    )

            except Exception:
                return None

            return None

        current_rates = load_fac(
            paths["fac_curr"],
            scenario_column,
        )

        previous_rates = load_fac(
            paths["fac_prev"],
            scenario_column,
        )

        fig_yield = go.Figure()

        if previous_rates is not None:
            previous_quarter_label = (
                cfg[
                    "target_info"
                ].get(
                    "previous_q",
                    "",
                )
            )

            previous_trace_name = (
                f"Previous Quarter "
                f"({previous_quarter_label})"
                if language == "English"
                else
                f"전분기 "
                f"({previous_quarter_label})"
            )

            fig_yield.add_trace(
                go.Scatter(
                    x=list(
                        range(
                            1,
                            len(previous_rates) + 1,
                        )
                    ),
                    y=previous_rates,
                    name=previous_trace_name,
                    line=dict(
                        color=SUPPORT[3],
                        dash="dash",
                        width=1.5,
                    ),
                    mode="lines",
                    hovertemplate=(
                        "<b>"
                        + previous_trace_name
                        + "</b><br>"
                        + (
                            "Month"
                            if language == "English"
                            else "월"
                        )
                        + ": %{x}<br>"
                        + (
                            "Rate"
                            if language == "English"
                            else "금리"
                        )
                        + ": %{y:.4f}%"
                        + "<extra></extra>"
                    ),
                )
            )

        if current_rates is not None:
            current_trace_name = (
                f"Current Quarter ({period_text})"
                if language == "English"
                else f"당분기 ({period_text})"
            )

            fig_yield.add_trace(
                go.Scatter(
                    x=list(
                        range(
                            1,
                            len(current_rates) + 1,
                        )
                    ),
                    y=current_rates,
                    name=current_trace_name,
                    line=dict(
                        color=C_DEEP_BLUE,
                        width=2,
                    ),
                    mode="lines",
                    hovertemplate=(
                        "<b>"
                        + current_trace_name
                        + "</b><br>"
                        + (
                            "Month"
                            if language == "English"
                            else "월"
                        )
                        + ": %{x}<br>"
                        + (
                            "Rate"
                            if language == "English"
                            else "금리"
                        )
                        + ": %{y:.4f}%"
                        + "<extra></extra>"
                    ),
                )
            )

        if (
            current_rates is None
            and previous_rates is None
        ):
            st.info(
                t(
                    "interest_rate_file_missing",
                    path=paths["fac_curr"],
                )
            )

        else:
            chart_title = t(
                "interest_rate_scenario_title",
                currency=economic_currency,
                period=period_text,
            )

            fig_yield.update_layout(
                title=chart_title,
                xaxis_title=(
                    "Month"
                    if language == "English"
                    else "Projection Month"
                ),
                yaxis_title=(
                    "Rate (%)"
                    if language == "English"
                    else "금리 (%)"
                ),
                height=400,
                paper_bgcolor=C_WHITE,
                plot_bgcolor=C_WHITE,
                font=dict(
                    color=PRIMARY[0],
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
                margin=dict(
                    t=60,
                    b=50,
                    l=60,
                    r=30,
                ),
            )

            fig_yield.update_yaxes(
                gridcolor=SUPPORT[7]
            )

            fig_yield.update_xaxes(
                gridcolor=SUPPORT[7]
            )

            st.plotly_chart(
                fig_yield,
                width="stretch",
                key="economic_yield_curve",
            )

            html_report.add_plotly(
                t(
                    "interest_rate_scenario",
                    currency=economic_currency,
                ),
                fig_yield,
                description=(
                    "Previous Quarter vs Current Quarter"
                    if language == "English"
                    else "전분기 대비 당분기"
                ),
            )

    # ════════════════════════════════════════════════════════════
    # 2. FA Spread
    # ════════════════════════════════════════════════════════════
    st.divider()

    st.subheader(
        t("fa_spread_analysis")
    )

    fa_spread_previous = load_fa_spread(
        paths["fa_spread_prev"]
    )

    fa_spread_current = load_fa_spread(
        paths["fa_spread_curr"]
    )

    if (
        not fa_spread_previous.empty
        or not fa_spread_current.empty
    ):
        fa_spread = safe_fillna(
            pd.merge(
                fa_spread_previous.rename(
                    columns={
                        "SPREAD": "Prev. Quarter",
                    }
                ),
                fa_spread_current.rename(
                    columns={
                        "SPREAD": "Curr. Quarter",
                    }
                ),
                on="PRODUCT",
                how="outer",
            )
        )

        fa_spread.insert(
            0,
            "Category",
            fa_spread.pop("PRODUCT"),
        )

        fa_spread["Diff"] = (
            fa_spread["Curr. Quarter"]
            - fa_spread["Prev. Quarter"]
        )

        fa_spread_display = fa_spread.copy()

        if language == "English":
            previous_display_column = "Previous Quarter"
            current_display_column = "Current Quarter"
            difference_display_column = "Difference"
        else:
            previous_display_column = "전분기"
            current_display_column = "당분기"
            difference_display_column = "차이"

        fa_spread_display = fa_spread_display.rename(
            columns={
                "Prev. Quarter": previous_display_column,
                "Curr. Quarter": current_display_column,
                "Diff": difference_display_column,
            }
        )

        for column_name in [
            previous_display_column,
            current_display_column,
        ]:
            fa_spread_display[column_name] = (
                fa_spread_display[
                    column_name
                ].map(
                    lambda value: (
                        f"{value * 100:.1f} bps"
                        if isinstance(
                            value,
                            (float, int),
                        )
                        else value
                    )
                )
            )

        fa_spread_display[
            difference_display_column
        ] = fa_spread_display[
            difference_display_column
        ].map(
            lambda value: (
                f"{value * 100:+.1f} bps"
                if isinstance(
                    value,
                    (float, int),
                )
                else value
            )
        )

        fa_spread_indexed = (
            fa_spread_display
            .set_index("Category")
        )

        st.dataframe(
            fa_spread_indexed.style
            .set_table_styles([
                {
                    "selector": "th",
                    "props": [
                        (
                            "text-align",
                            "center",
                        ),
                    ],
                }
            ]),
            width="stretch",
        )

        html_report.add_dataframe(
            t("fa_spread_analysis"),
            fa_spread_indexed,
            index=True,
        )

    else:
        st.info(
            t(
                "fa_spread_file_missing",
                path=paths["fa_spread_curr"],
            )
        )

    # ════════════════════════════════════════════════════════════
    # 3. Foreign Exchange Rate
    # ════════════════════════════════════════════════════════════
    st.subheader(
        t("fx_comparison")
    )

    fx_col_1, fx_col_2, fx_col_3 = st.columns(
        3
    )

    fx_col_1.metric(
        t("prev_quarter_avg"),
        f"{previous_fx_rate:,.1f} ₩/$",
    )

    fx_col_2.metric(
        t("curr_quarter_avg"),
        f"{current_fx_rate:,.1f} ₩/$",
        f"{current_fx_rate - previous_fx_rate:+,.1f} ₩/$",
    )

    fx_change_percentage = (
        (
            current_fx_rate
            / previous_fx_rate
            - 1
        )
        * 100
        if previous_fx_rate
        else 0.0
    )

    fx_col_3.metric(
        t("change_percent"),
        f"{fx_change_percentage:+.2f}%",
    )

    html_report.add_kpis(
        t("fx_comparison"),
        [
            (
                t("prev_quarter_avg"),
                f"{previous_fx_rate:,.1f} ₩/$",
                None,
            ),
            (
                t("curr_quarter_avg"),
                f"{current_fx_rate:,.1f} ₩/$",
                (
                    f"{current_fx_rate - previous_fx_rate:+,.1f} ₩/$"
                ),
            ),
            (
                t("change_percent"),
                f"{fx_change_percentage:+.2f}%",
                None,
            ),
        ],
    )