"""
tabs/summary.py
───────────────
Summary 탭.

기능
----
- Company Total VNB Walk
- KPI 카드
- 주요 Step Impact
- 채널별 ANP 및 Margin 카드
- 채널 기여도 및 Margin 차트
- Quarterly / Product Group 비교표
- Korean / English UI
- 자동 분석 및 저장 노트
- 오프라인 HTML Export
"""

from __future__ import annotations

from html import escape
from textwrap import dedent

import pandas as pd
import streamlit as st

from utils.auto_analysis import generate_summary_draft
from utils.charts import (
    compute_step_impacts,
    create_waterfall_chart,
)
from utils.charts_extra import (
    channel_contribution_bar,
    margin_scatter,
)
from utils.components import (
    build_summary_kpis,
    render_kpi_cards,
)
from utils.note import render_note_section
from utils.processor import calc_ticket_size_v2
from utils.tables import (
    get_summary_table,
    render_step_detail_table,
)
from utils.util import safe_fillna


def _format_card_amount(
    value: float,
) -> str:
    """카드용 금액을 K 또는 M 단위로 표시한다."""
    absolute_value = abs(value)

    if absolute_value >= 1_000_000:
        return f"{absolute_value / 1_000_000:,.1f}M"

    if absolute_value >= 1_000:
        return f"{absolute_value / 1_000:,.0f}K"

    return f"{absolute_value:,.0f}"


def _build_step_impact_html(
    top_steps: list[tuple[str, float, float]],
    display_currency: str,
    language: str,
    tab_map: dict[str, tuple[str | None, str]],
) -> str:
    """HTML Export용 주요 Step Impact 카드를 생성한다."""
    if not top_steps:
        return ""

    cards: list[str] = []

    for rank, (
        step,
        amount_impact,
        margin_impact,
    ) in enumerate(top_steps, 1):
        tab_name, emoji = tab_map.get(
            step,
            (None, "🔹"),
        )

        sign = (
            "▲"
            if margin_impact > 0
            else (
                "▼"
                if margin_impact < 0
                else "→"
            )
        )

        color = (
            "#27ae60"
            if margin_impact > 0
            else (
                "#e74c3c"
                if margin_impact < 0
                else "#888888"
            )
        )

        amount_text = _format_card_amount(
            amount_impact
        )

        if tab_name:
            hint = (
                f"{emoji} Refer to the {escape(tab_name)} tab"
                if language == "English"
                else f"{emoji} {escape(tab_name)} 탭 참고"
            )
        else:
            hint = ""

        cards.append(
            dedent(
                f"""
                <div class="summary-html-card">
                    <div class="summary-html-card-caption">
                        Margin Impact #{rank}
                    </div>

                    <div class="summary-html-card-title">
                        {escape(step)}
                    </div>

                    <div
                        class="summary-html-card-value"
                        style="color: {color};"
                    >
                        {sign} {margin_impact:+.2f}%p
                    </div>

                    <div class="summary-html-card-detail">
                        {escape(display_currency)}
                        {sign}
                        {escape(amount_text)}
                    </div>

                    <div class="summary-html-card-hint">
                        {hint}
                    </div>
                </div>
                """
            ).strip()
        )

    return dedent(
        f"""
        <div class="summary-html-card-grid">
            {''.join(cards)}
        </div>

        <style>
            .summary-html-card-grid {{
                display: grid;
                grid-template-columns:
                    repeat(auto-fit, minmax(210px, 1fr));
                gap: 14px;
            }}

            .summary-html-card {{
                padding: 16px;
                text-align: center;
                background: #fafbfc;
                border: 1px solid #d7e0e5;
                border-radius: 10px;
            }}

            .summary-html-card-caption {{
                color: #94a3b8;
                font-size: 11px;
            }}

            .summary-html-card-title {{
                margin: 5px 0;
                color: #003652;
                font-size: 16px;
                font-weight: 700;
            }}

            .summary-html-card-value {{
                font-size: 18px;
                font-weight: 700;
            }}

            .summary-html-card-detail {{
                margin-top: 4px;
                color: #475569;
                font-size: 13px;
            }}

            .summary-html-card-hint {{
                min-height: 18px;
                margin-top: 7px;
                color: #64748b;
                font-size: 11px;
            }}
        </style>
        """
    ).strip()


def _build_channel_card_html(
    channel_rows: pd.DataFrame,
    display_currency: str,
) -> str:
    """HTML Export용 채널별 ANP 및 Margin 카드를 생성한다."""
    if channel_rows.empty:
        return ""

    cards: list[str] = []

    for channel_name, row in channel_rows.iterrows():
        current_anp = float(
            row[("CURR", "ANP")]
        )
        anp_difference = float(
            row[("DIFF", "ANP")]
        )
        current_margin = float(
            row[("CURR", "VNB%")]
        )
        margin_difference = float(
            row[("DIFF", "VNB%")]
        )

        anp_sign = (
            "▲"
            if anp_difference > 0
            else (
                "▼"
                if anp_difference < 0
                else "→"
            )
        )

        margin_sign = (
            "▲"
            if margin_difference > 0
            else (
                "▼"
                if margin_difference < 0
                else "→"
            )
        )

        anp_color = (
            "#27ae60"
            if anp_difference > 0
            else (
                "#e74c3c"
                if anp_difference < 0
                else "#888888"
            )
        )

        margin_color = (
            "#27ae60"
            if margin_difference > 0
            else (
                "#e74c3c"
                if margin_difference < 0
                else "#888888"
            )
        )

        current_anp_text = _format_card_amount(
            current_anp
        )
        anp_difference_text = _format_card_amount(
            anp_difference
        )

        cards.append(
            dedent(
                f"""
                <div class="summary-html-card">
                    <div class="summary-html-card-title">
                        {escape(str(channel_name))}
                    </div>

                    <div class="summary-html-card-caption">
                        ANP
                    </div>

                    <div class="summary-html-card-detail-strong">
                        {escape(display_currency)}
                        {current_anp_text}
                    </div>

                    <div
                        class="summary-html-card-change"
                        style="color: {anp_color};"
                    >
                        {anp_sign}
                        {escape(display_currency)}
                        {anp_difference_text}
                    </div>

                    <div class="summary-html-card-caption margin-label">
                        Margin
                    </div>

                    <div class="summary-html-card-detail-strong">
                        {current_margin:.2f}%
                    </div>

                    <div
                        class="summary-html-card-change"
                        style="color: {margin_color};"
                    >
                        {margin_sign}
                        {margin_difference:+.2f}%p
                    </div>
                </div>
                """
            ).strip()
        )

    return dedent(
        f"""
        <div class="summary-html-card-grid">
            {''.join(cards)}
        </div>

        <style>
            .summary-html-card-detail-strong {{
                margin-top: 2px;
                color: #003652;
                font-size: 15px;
                font-weight: 650;
            }}

            .summary-html-card-change {{
                margin-top: 3px;
                font-size: 13px;
            }}

            .summary-html-card-caption.margin-label {{
                margin-top: 12px;
            }}
        </style>
        """
    ).strip()


def render(ctx) -> None:
    """Summary 탭을 렌더링한다."""
    language = ctx.language
    t = ctx.t
    html_report = ctx.html_report

    df_vnb_prev_conv = ctx.df_vnb_prev_conv
    df_vnb_curr_conv = ctx.df_vnb_curr_conv
    df_vnb_res_conv = ctx.df_vnb_res_conv

    df_mpf_prev_conv = ctx.df_mpf_prev_conv
    df_mpf_curr_conv = ctx.df_mpf_curr_conv

    display_currency = ctx.display_currency
    step_order = ctx.STEP_ORDER
    fx_unit_suffix = ctx.fx_unit_suffix
    unit_label = ctx.unit_label

    show_kpi = ctx.show_kpi
    show_charts = ctx.show_charts

    ct_pq_anp = ctx.CT_PQ_ANP
    ct_cq_anp = ctx.CT_CQ_ANP

    summary_format = ctx.SUMMARY_FMT
    th_center = ctx.TH_CENTER

    notes_file = ctx.NOTES_FILE

    current_fx_rate = ctx.CURR_FX_RATE
    previous_fx_rate = ctx.PREV_FX_RATE

    html_report.add_tab(
        t("tab_summary")
    )

    # ════════════════════════════════════════════════════════════
    # 1. Summary Table
    # ════════════════════════════════════════════════════════════
    comp_table = get_summary_table(
        "CHANNEL",
        df_vnb_prev_conv,
        df_vnb_curr_conv,
    )

    pg_table = get_summary_table(
        "PRODUCT_GROUP1",
        df_vnb_prev_conv,
        df_vnb_curr_conv,
    )

    channel_rows = comp_table.drop(
        index=[
            row_name
            for row_name in (
                "TOTAL (Company)",
                "Non-Model",
            )
            if row_name in comp_table.index
        ],
        errors="ignore",
    )

    # ════════════════════════════════════════════════════════════
    # 2. KPI
    # ════════════════════════════════════════════════════════════
    if show_kpi:
        kpis = build_summary_kpis(
            comp_table,
            pg_table,
            display_currency,
            t=t,
        )

        if kpis:
            render_kpi_cards(kpis)
            st.write("")

            html_report.add_kpis(
                (
                    "Key Performance Indicators"
                    if language == "English"
                    else "주요 성과 지표"
                ),
                [
                    (
                        kpi["label"],
                        kpi["value"],
                        kpi.get("delta"),
                    )
                    for kpi in kpis
                ],
            )

    # ════════════════════════════════════════════════════════════
    # 3. Company Total VNB Walk
    # ════════════════════════════════════════════════════════════
    st.subheader(
        t("company_total_vnb_walk")
    )

    total_walk_title = t(
        "total_vnb_movement"
    )

    fig_total_walk = create_waterfall_chart(
        df_vnb_res_conv,
        total_walk_title,
        step_order,
        display_currency,
        fx_unit_suffix,
        ct_pq_anp=ct_pq_anp,
        ct_cq_anp=ct_cq_anp,
        language=language,
    )

    st.plotly_chart(
        fig_total_walk,
        width="stretch",
        key="summary_total_waterfall",
    )

    html_report.add_plotly(
        t("company_total_vnb_walk"),
        fig_total_walk,
        description=unit_label,
    )

    step_detail = render_step_detail_table(
        df_vnb_res_conv,
        step_order,
        display_currency,
        ct_pq_anp=ct_pq_anp,
        ct_cq_anp=ct_cq_anp,
        t=t,
    )

    html_report.add_dataframe(
        (
            "VNB Walk Step Detail"
            if language == "English"
            else "VNB Walk Step 상세"
        ),
        step_detail,
        description=unit_label,
        index=True,
    )

    # ════════════════════════════════════════════════════════════
    # 4. 주요 Step Impact
    # ════════════════════════════════════════════════════════════
    impacts = compute_step_impacts(
        df_vnb_res_conv,
        step_order,
        ct_pq_anp=ct_pq_anp,
        ct_cq_anp=ct_cq_anp,
    )

    def get_impact(
        step_name: str,
    ) -> tuple[float, float]:
        return impacts.get(
            step_name,
            (0.0, 0.0),
        )

    pq_etu_amount, pq_etu_margin = get_impact(
        "PQ_ETU"
    )
    oth_etu_amount, oth_etu_margin = get_impact(
        "OTH_ETU"
    )

    pq_tvog_amount, pq_tvog_margin = get_impact(
        "PQ_TVOG"
    )
    cq_tvog_amount, cq_tvog_margin = get_impact(
        "CQ_TVOG"
    )

    pq_commission_amount, pq_commission_margin = get_impact(
        "PQ_COMM"
    )
    oth_commission_amount, oth_commission_margin = get_impact(
        "OTH_COMM"
    )

    net_etu_amount = (
        pq_etu_amount
        + oth_etu_amount
    )
    net_etu_margin = (
        pq_etu_margin
        + oth_etu_margin
    )

    net_tvog_amount = (
        pq_tvog_amount
        + cq_tvog_amount
    )
    net_tvog_margin = (
        pq_tvog_margin
        + cq_tvog_margin
    )

    net_commission_amount = (
        pq_commission_amount
        + oth_commission_amount
    )
    net_commission_margin = (
        pq_commission_margin
        + oth_commission_margin
    )

    excluded_raw_steps = {
        "PQ",
        "CQ",
        "PQ_ETU",
        "OTH_ETU",
        "PQ_TVOG",
        "CQ_TVOG",
        "PQ_COMM",
        "OTH_COMM",
    }

    step_impacts = {
        step_name: values
        for step_name, values in impacts.items()
        if step_name not in excluded_raw_steps
    }

    if net_etu_amount or net_etu_margin:
        step_impacts["NET_ETU"] = (
            net_etu_amount,
            net_etu_margin,
        )

    if net_tvog_amount or net_tvog_margin:
        step_impacts["NET_TVOG"] = (
            net_tvog_amount,
            net_tvog_margin,
        )

    if (
        net_commission_amount
        or net_commission_margin
    ):
        step_impacts["NET_COMM"] = (
            net_commission_amount,
            net_commission_margin,
        )

    tab_map = {
        "SL_VOL": ("Sales Mix", "📊"),
        "SL_MIX": ("Sales Mix", "📊"),
        "SL_DEMO": ("Demo", "👥"),
        "MC": (None, "🔄"),
        "EC_NMR": ("Economic", "📈"),
        "EC_FX": ("Economic", "📈"),
        "NET_COMM": ("Commission", "💰"),
        "NET_ETU": ("Expense", "🏢"),
        "NET_TVOG": (None, "📉"),
    }

    top_steps = sorted(
        step_impacts.items(),
        key=lambda item: abs(item[1][1]),
        reverse=True,
    )[:3]

    top_steps = [
        (
            step_name,
            amount_impact,
            margin_impact,
        )
        for step_name, (
            amount_impact,
            margin_impact,
        ) in top_steps
    ]

    if top_steps:
        st.markdown(
            f"#### {t('key_step_impact')}"
        )

        impact_columns = st.columns(
            len(top_steps)
        )

        for rank, (
            step_name,
            amount_impact,
            margin_impact,
        ) in enumerate(top_steps, 1):
            tab_name, emoji = tab_map.get(
                step_name,
                (None, "🔹"),
            )

            sign = (
                "▲"
                if margin_impact > 0
                else (
                    "▼"
                    if margin_impact < 0
                    else "→"
                )
            )

            color = (
                "#27ae60"
                if margin_impact > 0
                else (
                    "#e74c3c"
                    if margin_impact < 0
                    else "#888888"
                )
            )

            amount_text = _format_card_amount(
                amount_impact
            )

            hint = (
                t(
                    "refer_to_tab",
                    emoji=emoji,
                    tab_name=tab_name,
                )
                if tab_name
                else ""
            )

            impact_card_html = (
                f'<div style="'
                f'border:1px solid #cccccc;'
                f'border-radius:10px;'
                f'padding:14px 16px;'
                f'background:#fafbfc;'
                f'text-align:center;'
                f'">'
                f'<div style="font-size:0.72rem;color:#999999;">'
                f'Margin Impact #{rank}'
                f'</div>'
                f'<div style="font-weight:700;font-size:1.05rem;margin:4px 0;">'
                f'{step_name}'
                f'</div>'
                f'<div style="font-size:1.15rem;font-weight:700;color:{color};">'
                f'{sign} {margin_impact:+.2f}%p'
                f'</div>'
                f'<div style="font-size:0.82rem;color:#666666;margin-top:2px;">'
                f'{display_currency} {sign} {amount_text}'
                f'</div>'
                f'<div style="min-height:18px;font-size:0.75rem;'
                f'color:#888888;margin-top:6px;">'
                f'{hint}'
                f'</div>'
                f'</div>'
            )

            with impact_columns[rank - 1]:
                st.markdown(
                    impact_card_html,
                    unsafe_allow_html=True,
                )

        html_report.add_html(
            (
                "Key Step Impact by Margin"
                if language == "English"
                else "주요 Step Impact (Margin 기준)"
            ),
            _build_step_impact_html(
                top_steps,
                display_currency,
                language,
                tab_map,
            ),
        )

    # ════════════════════════════════════════════════════════════
    # 5. 채널별 ANP 및 Margin
    # ════════════════════════════════════════════════════════════
    if (
        not channel_rows.empty
        and ("CURR", "ANP") in channel_rows.columns
    ):
        st.markdown(
            f"#### {t('channel_anp_margin')}"
        )

        channel_detail = channel_rows.sort_values(
            ("CURR", "ANP"),
            ascending=False,
        )

        channel_names = (
            channel_detail.index.tolist()
        )

        columns_per_row = 4

        for row_start in range(
            0,
            len(channel_names),
            columns_per_row,
        ):
            channel_chunk = channel_names[
                row_start:
                row_start + columns_per_row
            ]

            channel_columns = st.columns(
                len(channel_chunk)
            )

            for column_index, channel_name in enumerate(
                channel_chunk
            ):
                row = channel_detail.loc[
                    channel_name
                ]

                current_anp = float(
                    row[("CURR", "ANP")]
                )
                anp_difference = float(
                    row[("DIFF", "ANP")]
                )
                current_margin = float(
                    row[("CURR", "VNB%")]
                )
                margin_difference = float(
                    row[("DIFF", "VNB%")]
                )

                anp_sign = (
                    "▲"
                    if anp_difference > 0
                    else (
                        "▼"
                        if anp_difference < 0
                        else "→"
                    )
                )

                margin_sign = (
                    "▲"
                    if margin_difference > 0
                    else (
                        "▼"
                        if margin_difference < 0
                        else "→"
                    )
                )

                anp_color = (
                    "#27ae60"
                    if anp_difference > 0
                    else (
                        "#e74c3c"
                        if anp_difference < 0
                        else "#888888"
                    )
                )

                margin_color = (
                    "#27ae60"
                    if margin_difference > 0
                    else (
                        "#e74c3c"
                        if margin_difference < 0
                        else "#888888"
                    )
                )

                current_anp_text = _format_card_amount(
                    current_anp
                )
                anp_difference_text = _format_card_amount(
                    anp_difference
                )

                channel_card_html = (
                    f'<div style="'
                    f'border:1px solid #cccccc;'
                    f'border-radius:10px;'
                    f'padding:14px 16px;'
                    f'background:#fafbfc;'
                    f'text-align:center;'
                    f'">'
                    f'<div style="font-weight:700;font-size:1.05rem;margin-bottom:6px;">'
                    f'{channel_name}'
                    f'</div>'
                    f'<div style="font-size:0.72rem;color:#999999;">'
                    f'ANP'
                    f'</div>'
                    f'<div style="font-size:1rem;font-weight:600;margin:2px 0;">'
                    f'{display_currency} {current_anp_text}'
                    f'</div>'
                    f'<div style="font-size:0.85rem;color:{anp_color};margin-bottom:8px;">'
                    f'{anp_sign} {display_currency} {anp_difference_text}'
                    f'</div>'
                    f'<div style="font-size:0.72rem;color:#999999;">'
                    f'Margin'
                    f'</div>'
                    f'<div style="font-size:1rem;font-weight:600;margin:2px 0;">'
                    f'{current_margin:.2f}%'
                    f'</div>'
                    f'<div style="font-size:0.85rem;color:{margin_color};">'
                    f'{margin_sign} {margin_difference:+.2f}%p'
                    f'</div>'
                    f'</div>'
                )

                with channel_columns[column_index]:
                    st.markdown(
                        channel_card_html,
                        unsafe_allow_html=True,
                    )

        html_report.add_html(
            (
                "ANP and Margin by Channel"
                if language == "English"
                else "채널별 ANP 및 Margin"
            ),
            _build_channel_card_html(
                channel_detail,
                display_currency,
            ),
        )

    # ════════════════════════════════════════════════════════════
    # 6. 보조 차트
    # ════════════════════════════════════════════════════════════
    if show_charts:
        st.divider()

        fig_channel_contribution = (
            channel_contribution_bar(
                comp_table,
                language=language,
            )
        )

        fig_margin_analysis = margin_scatter(
            comp_table,
            language=language,
        )

        chart_column_1, chart_column_2 = st.columns(
            [1, 1]
        )

        with chart_column_1:
            st.plotly_chart(
                fig_channel_contribution,
                width="stretch",
                key="sum_ch_contrib",
            )

        with chart_column_2:
            st.plotly_chart(
                fig_margin_analysis,
                width="stretch",
                key="sum_margin_scatter",
            )

        html_report.add_plotly(
            (
                "Channel VNB Contribution"
                if language == "English"
                else "채널별 VNB 기여도"
            ),
            fig_channel_contribution,
        )

        html_report.add_plotly(
            (
                "Channel Margin Analysis"
                if language == "English"
                else "채널별 Margin 분석"
            ),
            fig_margin_analysis,
        )

    # ════════════════════════════════════════════════════════════
    # 7. Performance Tables
    # ════════════════════════════════════════════════════════════
    st.divider()

    st.subheader(
        t("quarterly_performance")
    )
    st.caption(
        unit_label
    )

    st.dataframe(
        comp_table.style
        .format(summary_format)
        .set_table_styles(th_center),
        width="stretch",
    )

    html_report.add_dataframe(
        t("quarterly_performance"),
        comp_table,
        description=unit_label,
        index=True,
    )

    st.subheader(
        t("product_group_performance")
    )
    st.caption(
        unit_label
    )

    st.dataframe(
        pg_table.style
        .format(summary_format)
        .set_table_styles(th_center),
        width="stretch",
        key="summary_pg_compare_table",
    )

    html_report.add_dataframe(
        t("product_group_performance"),
        pg_table,
        description=unit_label,
        index=True,
    )

    # ════════════════════════════════════════════════════════════
    # 8. Analysis Report
    # ════════════════════════════════════════════════════════════
    st.divider()

    st.subheader(
        t("analysis_report")
    )

    ticket_size_previous = (
        calc_ticket_size_v2(
            df_mpf_prev_conv
        )
        .rename(
            columns={
                "Ticket Size": "Prev. TS",
            }
        )
    )

    ticket_size_current = (
        calc_ticket_size_v2(
            df_mpf_curr_conv
        )
        .rename(
            columns={
                "Ticket Size": "Curr. TS",
            }
        )
    )

    ticket_size_comparison = safe_fillna(
        pd.merge(
            ticket_size_previous,
            ticket_size_current,
            on="PRODUCT",
            how="outer",
        )
    )

    ticket_size_comparison["Growth(%)"] = (
        (
            ticket_size_comparison["Curr. TS"]
            / ticket_size_comparison["Prev. TS"]
            - 1
        )
        * 100
    ).replace(
        [
            float("inf"),
            float("-inf"),
        ],
        0,
    ).fillna(0)

    economic_information = {
        "rate_change": 0.0,
        "fx_change": (
            current_fx_rate
            - previous_fx_rate
        ),
    }

    summary_draft = generate_summary_draft(
        df_vnb_res_conv,
        comp_table,
        pg_table,
        display_currency,
        step_order,
        ts_comp=ticket_size_comparison,
        economic_info=economic_information,
        language=language,
    )

    final_analysis = render_note_section(
        tab_name="Summary",
        keys=["Company Total"],
        NOTES_FILE=notes_file,
        auto_draft=summary_draft,
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
        description=(
            "Company Total"
            if language == "English"
            else "전사 기준"
        ),
    )