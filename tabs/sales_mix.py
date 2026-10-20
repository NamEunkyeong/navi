"""
tabs/sales_mix.py
─────────────────
Sales Mix 탭.

기능
----
- Product Group × Channel 필터
- VNB Walk
- Channel / Product / Contract Type Mix 비교
- Korean / English UI
- 자동 분석 및 저장 노트
- 오프라인 HTML Export
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.auto_analysis import generate_sales_mix_draft
from utils.charts import create_waterfall_chart
from utils.charts_extra import mix_compare_bar
from utils.note import render_note_section
from utils.processor import (
    filter_data,
    get_contract_type_mix,
    get_dim_mix,
)
from utils.tables import (
    get_summary_table,
    highlight_top_abs_diff,
    render_step_detail_table,
)
from utils.util import (
    format_value,
    safe_fillna,
)


def render(ctx) -> None:
    """Sales Mix 탭을 렌더링한다."""
    # ── 언어 및 HTML Export ───────────────────────────────────
    language = ctx.language
    t = ctx.t
    html_report = ctx.html_report

    # ── Context ───────────────────────────────────────────────
    pg_opts = ctx.pg_opts
    ch_opts = ctx.ch_opts

    year = ctx.year
    quarter = ctx.quarter

    fx_rate = ctx.fx_rate
    display_currency = ctx.display_currency

    step_order = ctx.STEP_ORDER
    fx_unit_suffix = ctx.fx_unit_suffix
    unit_label = ctx.unit_label

    show_charts = ctx.show_charts

    ct_pq_anp = ctx.CT_PQ_ANP
    ct_cq_anp = ctx.CT_CQ_ANP

    th_center = ctx.TH_CENTER
    notes_file = ctx.NOTES_FILE

    df_mpf_curr_conv = ctx.df_mpf_curr_conv
    df_mpf_prev_conv = ctx.df_mpf_prev_conv

    df_vnb_curr_conv = ctx.df_vnb_curr_conv
    df_vnb_prev_conv = ctx.df_vnb_prev_conv

    df_vnb_prev_full_raw = ctx.df_vnb_prev_full_raw
    df_vnb_curr_full_raw = ctx.df_vnb_curr_full_raw
    df_vnb_res_raw = ctx.df_vnb_res_raw

    cached_filtered_walk = ctx.cached_filtered_walk

    # HTML Report에서 새 탭 시작
    html_report.add_tab(
        t("tab_sales_mix")
    )

    # ════════════════════════════════════════════════════════════
    # 1. Filter
    # ════════════════════════════════════════════════════════════
    st.subheader(
        t("filter")
    )

    col_filter_1, col_filter_2, _ = st.columns(
        [2, 2, 4]
    )

    with col_filter_1:
        target_pg_sm = st.selectbox(
            t("product_group"),
            pg_opts,
            key="sm_pg_filter",
        )

    with col_filter_2:
        target_ch_sm = st.selectbox(
            t("channel"),
            ch_opts,
            key="sm_ch_filter",
        )

    scope_label = (
        f"{target_pg_sm} × {target_ch_sm}"
    )

    # ════════════════════════════════════════════════════════════
    # 2. 선택 범위 데이터 계산
    # ════════════════════════════════════════════════════════════
    vnb_sm = cached_filtered_walk(
        df_vnb_prev_full_raw,
        df_vnb_curr_full_raw,
        df_vnb_res_raw,
        year,
        quarter,
        target_ch_sm,
        target_pg_sm,
        fx_rate,
        display_currency,
    )

    curr_sm = filter_data(
        df_mpf_curr_conv,
        target_pg_sm,
        target_ch_sm,
    )

    prev_sm = filter_data(
        df_mpf_prev_conv,
        target_pg_sm,
        target_ch_sm,
    )

    # 선택 상품군 내 채널별 Margin 비교
    vnb_curr_pg_scope = filter_data(
        df_vnb_curr_conv,
        target_pg_sm,
        "Company Total",
    )

    vnb_prev_pg_scope = filter_data(
        df_vnb_prev_conv,
        target_pg_sm,
        "Company Total",
    )

    comp_table_sm = get_summary_table(
        "CHANNEL",
        vnb_prev_pg_scope,
        vnb_curr_pg_scope,
    )

    # 선택 채널 내 상품군별 Margin 비교
    vnb_curr_ch_scope = filter_data(
        df_vnb_curr_conv,
        "Company Total",
        target_ch_sm,
    )

    vnb_prev_ch_scope = filter_data(
        df_vnb_prev_conv,
        "Company Total",
        target_ch_sm,
    )

    pg_table_sm = get_summary_table(
        "PRODUCT_GROUP1",
        vnb_prev_ch_scope,
        vnb_curr_ch_scope,
    )

    # ════════════════════════════════════════════════════════════
    # 3. VNB Walk
    # ════════════════════════════════════════════════════════════
    waterfall_title = t(
        "vnb_walk_scope",
        scope=scope_label,
    )

    fig_sm_waterfall = create_waterfall_chart(
        vnb_sm,
        waterfall_title,
        step_order,
        display_currency,
        fx_unit_suffix,
        ct_pq_anp=ct_pq_anp,
        ct_cq_anp=ct_cq_anp,
        language=language,
    )

    st.plotly_chart(
        fig_sm_waterfall,
        width="stretch",
        key="sm_waterfall",
    )

    html_report.add_plotly(
        waterfall_title,
        fig_sm_waterfall,
        description=unit_label,
    )

    step_detail_sm = render_step_detail_table(
        vnb_sm,
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
        step_detail_sm,
        description=unit_label,
        index=True,
    )

    st.divider()

    # ════════════════════════════════════════════════════════════
    # 4. Channel Mix
    # ════════════════════════════════════════════════════════════
    ch_mix_p = (
        get_dim_mix(
            prev_sm,
            "CHANNEL",
        )
        .rename(
            columns={
                "Mix(%)": "Prev. Mix(%)",
                "ANP": "Prev. ANP",
            }
        )
    )

    ch_mix_c = (
        get_dim_mix(
            curr_sm,
            "CHANNEL",
        )
        .rename(
            columns={
                "Mix(%)": "Curr. Mix(%)",
                "ANP": "Curr. ANP",
            }
        )
    )

    ch_comp = safe_fillna(
        pd.merge(
            ch_mix_p,
            ch_mix_c,
            on="CHANNEL",
            how="outer",
        )
    )

    ch_comp["Diff(%p)"] = (
        ch_comp["Curr. Mix(%)"]
        - ch_comp["Prev. Mix(%)"]
    )

    with st.expander(
        t("channel_mix_analysis"),
        expanded=False,
    ):
        if (
            show_charts
            and not ch_comp.empty
        ):
            channel_mix_title = t(
                "channel_mix_chart"
            )

            fig_channel_mix = mix_compare_bar(
                ch_comp,
                "CHANNEL",
                channel_mix_title,
                language=language,
            )

            st.plotly_chart(
                fig_channel_mix,
                width="stretch",
                key="sm_ch_bar",
            )

            html_report.add_plotly(
                channel_mix_title,
                fig_channel_mix,
            )

        st.caption(
            unit_label
        )

        st.dataframe(
            ch_comp.style
            .format({
                "Prev. ANP": (
                    lambda value:
                    format_value(
                        value,
                        "amount",
                    )
                ),
                "Curr. ANP": (
                    lambda value:
                    format_value(
                        value,
                        "amount",
                    )
                ),
                "Prev. Mix(%)": (
                    lambda value:
                    format_value(
                        value,
                        "percent",
                    )
                ),
                "Curr. Mix(%)": (
                    lambda value:
                    format_value(
                        value,
                        "percent",
                    )
                ),
                "Diff(%p)": (
                    lambda value:
                    format_value(
                        value,
                        "diff_percent",
                    )
                ),
            })
            .set_table_styles(
                th_center
            ),
            width="stretch",
        )

    html_report.add_dataframe(
        (
            "Channel Mix Comparison"
            if language == "English"
            else "Channel Mix 비교"
        ),
        ch_comp,
        description=unit_label,
        index=False,
    )

    # ════════════════════════════════════════════════════════════
    # 5. Product Portfolio Mix
    # ════════════════════════════════════════════════════════════
    product_column = next(
        (
            column
            for column in [
                "PRODUCT",
                "PROD_NAME_MP",
                "PROD_NAME_BASE",
            ]
            if column in curr_sm.columns
        ),
        "PRODUCT",
    )

    pg_mix_p = (
        get_dim_mix(
            prev_sm,
            product_column,
        )
        .rename(
            columns={
                "Mix(%)": "Prev. Mix(%)",
                "ANP": "Prev. ANP",
            }
        )
    )

    pg_mix_c = (
        get_dim_mix(
            curr_sm,
            product_column,
        )
        .rename(
            columns={
                "Mix(%)": "Curr. Mix(%)",
                "ANP": "Curr. ANP",
            }
        )
    )

    pg_comp = safe_fillna(
        pd.merge(
            pg_mix_p,
            pg_mix_c,
            on=product_column,
            how="outer",
        )
    )

    if product_column != "PRODUCT":
        pg_comp = pg_comp.rename(
            columns={
                product_column: "PRODUCT",
            }
        )

    pg_comp["Diff(%p)"] = (
        pg_comp["Curr. Mix(%)"]
        - pg_comp["Prev. Mix(%)"]
    )

    pg_comp_sorted = pg_comp.reindex(
        pg_comp["Diff(%p)"]
        .abs()
        .sort_values(ascending=False)
        .index
    ).reset_index(drop=True)

    with st.expander(
        t("product_portfolio_mix"),
        expanded=False,
    ):
        if (
            show_charts
            and not pg_comp_sorted.empty
        ):
            product_mix_title = t(
                "product_mix_chart"
            )

            fig_product_mix = mix_compare_bar(
                pg_comp_sorted,
                "PRODUCT",
                product_mix_title,
                language=language,
            )

            st.plotly_chart(
                fig_product_mix,
                width="stretch",
                key="sm_pg_bar",
            )

            html_report.add_plotly(
                product_mix_title,
                fig_product_mix,
            )

        st.caption(
            t("top_four_highlight")
        )

        st.caption(
            unit_label
        )

        st.dataframe(
            pg_comp_sorted.style
            .format({
                "Prev. ANP": (
                    lambda value:
                    format_value(
                        value,
                        "amount",
                    )
                ),
                "Curr. ANP": (
                    lambda value:
                    format_value(
                        value,
                        "amount",
                    )
                ),
                "Prev. Mix(%)": (
                    lambda value:
                    format_value(
                        value,
                        "percent",
                    )
                ),
                "Curr. Mix(%)": (
                    lambda value:
                    format_value(
                        value,
                        "percent",
                    )
                ),
                "Diff(%p)": (
                    lambda value:
                    format_value(
                        value,
                        "diff_percent",
                    )
                ),
            })
            .apply(
                highlight_top_abs_diff(
                    pg_comp_sorted,
                    "Diff(%p)",
                    top_n=4,
                ),
                axis=1,
            )
            .set_table_styles(
                th_center
            ),
            width="stretch",
        )

    html_report.add_dataframe(
        (
            "Product Portfolio Mix"
            if language == "English"
            else "상품 포트폴리오 Mix"
        ),
        pg_comp_sorted,
        description=unit_label,
        index=False,
    )

    # ════════════════════════════════════════════════════════════
    # 6. Contract Type Mix
    # ════════════════════════════════════════════════════════════
    ct_comp = get_contract_type_mix(
        prev_sm,
        curr_sm,
    )

    with st.expander(
        t("contract_type_mix"),
        expanded=False,
    ):
        if not ct_comp.empty:
            if show_charts:
                contract_type_title = t(
                    "contract_type_mix_chart"
                )

                fig_contract_type_mix = mix_compare_bar(
                    ct_comp,
                    "CONTRACT_TYPE",
                    contract_type_title,
                    language=language,
                )

                st.plotly_chart(
                    fig_contract_type_mix,
                    width="stretch",
                    key="sm_ct_bar",
                )

                html_report.add_plotly(
                    contract_type_title,
                    fig_contract_type_mix,
                )

            st.caption(
                unit_label
            )

            st.dataframe(
                ct_comp.style
                .format({
                    "Prev. ANP": (
                        lambda value:
                        format_value(
                            value,
                            "amount",
                        )
                    ),
                    "Curr. ANP": (
                        lambda value:
                        format_value(
                            value,
                            "amount",
                        )
                    ),
                    "Prev. Mix(%)": (
                        lambda value:
                        format_value(
                            value,
                            "percent",
                        )
                    ),
                    "Curr. Mix(%)": (
                        lambda value:
                        format_value(
                            value,
                            "percent",
                        )
                    ),
                    "Diff(%p)": (
                        lambda value:
                        format_value(
                            value,
                            "diff_percent",
                        )
                    ),
                })
                .set_table_styles(
                    th_center
                ),
                width="stretch",
            )

    html_report.add_dataframe(
        (
            "Contract Type Mix"
            if language == "English"
            else "계약 유형 Mix"
        ),
        ct_comp,
        description=unit_label,
        index=False,
    )

    # ════════════════════════════════════════════════════════════
    # 7. Analysis Report
    # ════════════════════════════════════════════════════════════
    st.divider()

    st.subheader(
        t("analysis_report")
    )

    sales_mix_draft = generate_sales_mix_draft(
        target_pg_sm,
        target_ch_sm,
        ch_comp,
        pg_comp_sorted,
        vnb_sm,
        display_currency,
        step_order,
        mix_threshold=1.0,
        ct_comp=ct_comp,
        comp_table=comp_table_sm,
        pg_table=pg_table_sm,
        ct_pq_anp=ct_pq_anp,
        ct_cq_anp=ct_cq_anp,
        language=language,
    )

    final_analysis = render_note_section(
        tab_name="SalesMix",
        keys=[
            target_pg_sm,
            target_ch_sm,
        ],
        NOTES_FILE=notes_file,
        auto_draft=sales_mix_draft,
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
        description=scope_label,
    )