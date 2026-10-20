"""
tabs/commission.py
──────────────────
Commission 탭.

기능
----
- 채널 / 상품별 Commission Rate 비교
- Plan / PQ / CQ 비교 차트
- Korean / English UI
- 자동 분석 및 저장 노트
- 오프라인 HTML Export
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from styles.theme import (
    C_DEEP_BLUE,
    C_LIGHT_BLUE,
    SUPPORT,
)
from utils.auto_analysis import generate_commission_draft
from utils.note import render_note_section
from utils.processor import get_comm_data
from utils.tables import highlight_top_abs_diff


def render(ctx) -> None:
    """Commission 탭을 렌더링한다."""
    # ── 언어 및 HTML Export ───────────────────────────────────
    language = ctx.language
    t = ctx.t
    html_report = ctx.html_report

    # ── Context ───────────────────────────────────────────────
    paths = ctx.paths
    display_currency = ctx.display_currency
    show_charts = ctx.show_charts

    th_center = ctx.TH_CENTER
    notes_file = ctx.NOTES_FILE

    df_comm_curr_raw = ctx.df_comm_curr_raw
    df_comm_prev_raw = ctx.df_comm_prev_raw

    html_report.add_tab(
        t("tab_commission")
    )

    # ════════════════════════════════════════════════════════════
    # 1. Commission Data
    # ════════════════════════════════════════════════════════════
    st.subheader(
        t("commission_rate_analysis")
    )

    st.caption(
        t("commission_unit")
    )

    df_comm_all = get_comm_data(
        df_comm_curr_raw,
        df_comm_prev_raw,
        lob_mapping_path=paths.get(
            "lob_mapping",
            "",
        ),
    )

    # ════════════════════════════════════════════════════════════
    # 2. Channel / Product Filter
    # ════════════════════════════════════════════════════════════
    if "CHANNEL" in df_comm_curr_raw.columns:
        commission_channels = (
            ["All"]
            + sorted(
                df_comm_curr_raw[
                    "CHANNEL"
                ].dropna().unique().tolist()
            )
        )
    else:
        commission_channels = ["All"]

    col_comm_channel, col_comm_product = st.columns(2)

    with col_comm_channel:
        target_ch_comm = st.selectbox(
            t("select_channel"),
            commission_channels,
            key="comm_ch",
        )

    if (
        target_ch_comm != "All"
        and "CHANNEL" in df_comm_all.columns
    ):
        df_comm_channel = df_comm_all[
            df_comm_all["CHANNEL"] == target_ch_comm
        ]
    else:
        df_comm_channel = df_comm_all

    if "PRODUCT" in df_comm_channel.columns:
        commission_products = (
            ["All"]
            + sorted(
                df_comm_channel[
                    "PRODUCT"
                ].dropna().unique().tolist()
            )
        )
    else:
        commission_products = ["All"]

    with col_comm_product:
        target_prod_comm = st.selectbox(
            t("select_product"),
            commission_products,
            key=f"comm_prod_{target_ch_comm}",
        )

    if (
        target_prod_comm != "All"
        and "PRODUCT" in df_comm_channel.columns
    ):
        df_comm_final = df_comm_channel[
            df_comm_channel["PRODUCT"] == target_prod_comm
        ]
    else:
        df_comm_final = df_comm_channel

    df_comm_final = df_comm_final.copy()

    # CQ-PLAN 절대값 내림차순 정렬
    if (
        not df_comm_final.empty
        and "CQ-PLAN" in df_comm_final.columns
    ):
        df_comm_final = df_comm_final.reindex(
            df_comm_final[
                "CQ-PLAN"
            ].abs().sort_values(
                ascending=False
            ).index
        ).reset_index(drop=True)

    if target_prod_comm == "All":
        commission_scope = target_ch_comm
    else:
        commission_scope = (
            f"{target_ch_comm} / "
            f"{target_prod_comm}"
        )

    # ════════════════════════════════════════════════════════════
    # 3. Commission Table
    # ════════════════════════════════════════════════════════════
    if not df_comm_final.empty:
        percent_formatter = (
            lambda value: f"{value:.2f}%"
        )

        difference_formatter = (
            lambda value: f"{value:+.2f}%p"
        )

        st.caption(
            t("commission_highlight")
        )

        format_columns = {}

        if "PLAN(%)" in df_comm_final.columns:
            format_columns["PLAN(%)"] = percent_formatter

        if "PQ(%)" in df_comm_final.columns:
            format_columns["PQ(%)"] = percent_formatter

        if "CQ(%)" in df_comm_final.columns:
            format_columns["CQ(%)"] = percent_formatter

        if "CQ-PQ" in df_comm_final.columns:
            format_columns["CQ-PQ"] = difference_formatter

        if "CQ-PLAN" in df_comm_final.columns:
            format_columns["CQ-PLAN"] = difference_formatter

        commission_styler = (
            df_comm_final.style
            .format(format_columns)
        )

        if "CQ-PLAN" in df_comm_final.columns:
            commission_styler = commission_styler.apply(
                highlight_top_abs_diff(
                    df_comm_final,
                    "CQ-PLAN",
                    top_n=4,
                ),
                axis=1,
            )

        commission_styler = (
            commission_styler
            .set_table_styles(th_center)
        )

        st.dataframe(
            commission_styler,
            width="stretch",
        )

        html_report.add_dataframe(
            (
                f"Commission Rate Comparison · "
                f"{commission_scope}"
                if language == "English"
                else
                f"Commission Rate 비교 · "
                f"{commission_scope}"
            ),
            df_comm_final,
            description=t("commission_unit"),
            index=False,
        )

        # ════════════════════════════════════════════════════════
        # 4. Commission Chart
        # ════════════════════════════════════════════════════════
        if (
            show_charts
            and "CQ(%)" in df_comm_final.columns
        ):
            group_column = (
                "PRODUCT"
                if "PRODUCT" in df_comm_final.columns
                else "PLICD"
            )

            required_rate_columns = [
                column
                for column in [
                    "PLAN(%)",
                    "PQ(%)",
                    "CQ(%)",
                ]
                if column in df_comm_final.columns
            ]

            df_comm_chart = (
                df_comm_final
                .groupby(
                    group_column,
                    as_index=False,
                )[required_rate_columns]
                .mean()
            )

            fig_commission = go.Figure()

            if "PLAN(%)" in df_comm_chart.columns:
                fig_commission.add_trace(
                    go.Bar(
                        x=df_comm_chart[group_column],
                        y=df_comm_chart["PLAN(%)"],
                        name="Plan",
                        marker_color=C_LIGHT_BLUE,
                        hovertemplate=(
                            "<b>%{x}</b><br>"
                            "Plan: %{y:.2f}%"
                            "<extra></extra>"
                        ),
                    )
                )

            if "PQ(%)" in df_comm_chart.columns:
                previous_label = (
                    "Previous Quarter"
                    if language == "English"
                    else "전분기"
                )

                fig_commission.add_trace(
                    go.Bar(
                        x=df_comm_chart[group_column],
                        y=df_comm_chart["PQ(%)"],
                        name=previous_label,
                        marker_color=SUPPORT[5],
                        hovertemplate=(
                            "<b>%{x}</b><br>"
                            f"{previous_label}: %{{y:.2f}}%"
                            "<extra></extra>"
                        ),
                    )
                )

            if "CQ(%)" in df_comm_chart.columns:
                current_label = (
                    "Current Quarter"
                    if language == "English"
                    else "당분기"
                )

                fig_commission.add_trace(
                    go.Bar(
                        x=df_comm_chart[group_column],
                        y=df_comm_chart["CQ(%)"],
                        name=current_label,
                        marker_color=C_DEEP_BLUE,
                        hovertemplate=(
                            "<b>%{x}</b><br>"
                            f"{current_label}: %{{y:.2f}}%"
                            "<extra></extra>"
                        ),
                    )
                )

            chart_title = (
                f"Commission Rate Analysis · "
                f"{commission_scope}"
                if language == "English"
                else
                f"Commission Rate 분석 · "
                f"{commission_scope}"
            )

            fig_commission.update_layout(
                title=chart_title,
                barmode="group",
                height=420,
                bargap=0.28,
                xaxis_title=(
                    "Product"
                    if language == "English"
                    else "상품"
                ),
                yaxis_title=(
                    "Commission Rate (%)"
                    if language == "English"
                    else "수수료율 (%)"
                ),
                yaxis_ticksuffix="%",
                paper_bgcolor="white",
                plot_bgcolor="white",
                font=dict(
                    color=C_DEEP_BLUE,
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                ),
            )

            st.plotly_chart(
                fig_commission,
                width="stretch",
                key="comm_pva",
            )

            html_report.add_plotly(
                chart_title,
                fig_commission,
            )

    else:
        st.info(
            t("commission_data_missing")
        )

    # ════════════════════════════════════════════════════════════════
    # 5. Analysis Report
    # ════════════════════════════════════════════════════════════════
    st.divider()

    st.subheader(
        t("analysis_report")
    )

    commission_draft = generate_commission_draft(
        target_ch=commission_scope,
        df_comm=df_comm_final,
        display_currency=display_currency,
        language=language,
    )

    # 생성 함수가 실수로 None을 반환하는 경우에도 원인을 화면에서
    # 바로 확인할 수 있도록 빈 문자열로 정규화한다.
    commission_draft = (
        str(commission_draft).strip()
        if commission_draft is not None
        else ""
    )

    if not commission_draft:
        commission_draft = (
            "## 💰 Commission Rate Analysis\n\n"
            "Commission analysis could not be generated. "
            "Please check the selected filters and commission data."
            if language == "English"
            else
            "## 💰 Commission Rate 분석\n\n"
            "Commission 자동 분석을 생성하지 못했습니다. "
            "선택한 필터와 Commission 데이터를 확인해주세요."
        )

    final_analysis = render_note_section(
        tab_name="Commission",
        keys=[
            target_ch_comm,
            target_prod_comm,
        ],
        NOTES_FILE=notes_file,
        auto_draft=commission_draft,
        language=language,
        t=t,
    )

    html_report.add_text(
        (
            "Analysis Report"
            if language == "English"
            else "분석 보고서"
        ),
        final_analysis,
        description=commission_scope,
    )