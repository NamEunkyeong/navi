"""
tabs/expense.py
───────────────
Expense 탭.

기능
----
- 채널 / Company Total 기준 Expense Actual vs Model 비교
- Korean / English UI
- 자동 분석 및 저장 노트
- 오프라인 HTML Export
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from styles.utils import (
    cmap_custom,
    get_normalized_gmap,
)
from utils.auto_analysis import generate_expense_draft
from utils.charts_extra import plan_vs_actual_bar
from utils.note import render_note_section
from utils.processor import (
    get_expense_data,
    load_actual_expense,
)


def render(ctx) -> None:
    """Expense 탭을 렌더링한다."""
    # ── 언어 및 HTML Export ───────────────────────────────────
    language = ctx.language
    t = ctx.t
    html_report = ctx.html_report

    # ── Context ───────────────────────────────────────────────
    display_currency = ctx.display_currency
    show_charts = ctx.show_charts

    th_center = ctx.TH_CENTER
    notes_file = ctx.NOTES_FILE
    unit_label = ctx.unit_label

    df_mpf_curr_conv = ctx.df_mpf_curr_conv
    df_exp_curr_raw = ctx.df_exp_curr_raw

    actual_expense_path = ctx.actual_expense_path

    html_report.add_tab(
        t("tab_expense")
    )

    # ════════════════════════════════════════════════════════════
    # 1. Scope Filter
    # ════════════════════════════════════════════════════════════
    st.subheader(
        t("expense_variance_analysis")
    )

    if "CHANNEL" in df_mpf_curr_conv.columns:
        expense_channels = (
            ["Company Total"]
            + sorted(
                df_mpf_curr_conv[
                    "CHANNEL"
                ].dropna().unique().tolist()
            )
        )
    else:
        expense_channels = [
            "Company Total"
        ]

    target_ch_exp = st.selectbox(
        t("channel_scope"),
        expense_channels,
        key="exp_scope",
    )

    # ════════════════════════════════════════════════════════════
    # 2. Expense Data
    # ════════════════════════════════════════════════════════════
    if not df_exp_curr_raw.empty:
        actual_current = load_actual_expense(
            actual_expense_path,
            channel=target_ch_exp,
        )

        df_exp_display = get_expense_data(
            df_exp_curr_raw,
            channel=target_ch_exp,
            actual_curr=actual_current,
        )

    else:
        df_exp_display = pd.DataFrame()

    # ════════════════════════════════════════════════════════════
    # 3. Expense Summary
    # ════════════════════════════════════════════════════════════
    if df_exp_display.empty:
        st.info(
            t("expense_data_missing")
        )

    else:
        expense_summary_title = t(
            "expense_summary",
            scope=target_ch_exp,
        )

        st.subheader(
            expense_summary_title
        )

        st.caption(
            unit_label
        )

        amount_formatter = (
            lambda value: f"{value:,.1f}"
        )

        difference_formatter = (
            lambda value: f"{value:+,.1f}"
        )

        ratio_formatter = (
            lambda value: f"{value:.4f}"
        )

        format_columns = {}

        for column_name in [
            "Actual",
            "Model",
        ]:
            if column_name in df_exp_display.columns:
                format_columns[
                    column_name
                ] = amount_formatter

        if "Actual / Model" in df_exp_display.columns:
            format_columns[
                "Actual / Model"
            ] = ratio_formatter

        if "Actual - Model" in df_exp_display.columns:
            format_columns[
                "Actual - Model"
            ] = difference_formatter

        if "AFT_TAX" in df_exp_display.columns:
            format_columns[
                "AFT_TAX"
            ] = difference_formatter

        expense_styler = (
            df_exp_display.style
            .format(format_columns)
        )

        if (
            "Actual / Model" in df_exp_display.columns
            and df_exp_display[
                "Actual / Model"
            ].fillna(0).any()
        ):
            expense_styler = (
                expense_styler
                .background_gradient(
                    subset=[
                        "Actual / Model",
                    ],
                    cmap=cmap_custom,
                    gmap=get_normalized_gmap(
                        df_exp_display[
                            "Actual / Model"
                        ]
                        - 1
                    ),
                )
            )

        st.dataframe(
            expense_styler.set_table_styles(
                th_center
            ),
            width="stretch",
        )

        st.caption(
            t("expense_note")
        )

        html_report.add_dataframe(
            expense_summary_title,
            df_exp_display,
            description=unit_label,
            index=True,
        )

        # ════════════════════════════════════════════════════════
        # 4. Actual vs Model Chart
        # ════════════════════════════════════════════════════════
        if show_charts:
            df_exp_chart = (
                df_exp_display
                .reset_index()
                .rename(
                    columns={
                        "index": "Category",
                    }
                )
            )

            df_exp_chart = df_exp_chart[
                df_exp_chart[
                    "Category"
                ].isin([
                    "ANP",
                    "PNI",
                    "SC",
                    "COMM",
                ])
            ]

            if not df_exp_chart.empty:
                expense_chart_title = t(
                    "expense_chart_title"
                )

                fig_expense = plan_vs_actual_bar(
                    df_exp_chart,
                    "Category",
                    "Model",
                    "Actual",
                    expense_chart_title,
                    language=language,
                )

                st.plotly_chart(
                    fig_expense,
                    width="stretch",
                    key="exp_pva",
                )

                html_report.add_plotly(
                    (
                        f"{expense_chart_title} · "
                        f"{target_ch_exp}"
                    ),
                    fig_expense,
                    description=unit_label,
                )

    # ════════════════════════════════════════════════════════════
    # 5. Analysis Report
    # ════════════════════════════════════════════════════════════
    st.divider()

    st.subheader(
        t("analysis_report")
    )

    expense_draft = generate_expense_draft(
        target_ch_exp,
        df_exp_display,
        display_currency,
        language=language,
    )

    final_analysis = render_note_section(
        tab_name="Expense",
        keys=[
            target_ch_exp,
        ],
        NOTES_FILE=notes_file,
        auto_draft=expense_draft,
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
        description=target_ch_exp,
    )