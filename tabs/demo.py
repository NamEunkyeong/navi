"""
tabs/demo.py
────────────
Demo 탭.

기능
----
- Product Group × Channel × Product 필터
- VNB Walk
- 상품 / Ticket Size / 납기 / 연령 / 거치기간 분석
- Korean / English UI
- 자동 분석 및 저장 노트
- 오프라인 HTML Export
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from utils.auto_analysis import generate_demo_draft
from utils.charts import create_waterfall_chart
from utils.charts_extra import (
    age_compare_bar,
    defer_compare_bar,
    product_mix_diff_bar,
    term_compare_bar,
)
from utils.note import render_note_section
from utils.processor import (
    calc_ticket_size_v2,
    filter_data,
    get_age_group_mix,
    get_defer_avg,
    get_defer_mix,
    get_dim_mix,
    get_term_mix,
)
from utils.tables import (
    highlight_top_abs_diff,
    render_step_detail_table,
)
from utils.util import (
    format_value,
    safe_fillna,
)


def render(ctx) -> None:
    """Demo 탭을 렌더링한다."""
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
    other_limit = ctx.OTHER_LIMIT

    df_mpf_curr_conv = ctx.df_mpf_curr_conv
    df_mpf_prev_conv = ctx.df_mpf_prev_conv

    df_vnb_prev_full_raw = ctx.df_vnb_prev_full_raw
    df_vnb_curr_full_raw = ctx.df_vnb_curr_full_raw
    df_vnb_res_raw = ctx.df_vnb_res_raw

    cached_filtered_walk = ctx.cached_filtered_walk

    # HTML Report의 Demo 탭 시작
    html_report.add_tab(
        t("tab_demo")
    )

    # ════════════════════════════════════════════════════════════
    # 1. Filter
    # ════════════════════════════════════════════════════════════
    st.subheader(
        t("filter")
    )

    col_demo_pg, col_demo_product, col_demo_channel, _ = st.columns(
        [2, 2, 2, 2]
    )

    with col_demo_pg:
        target_pg_dm = st.selectbox(
            t("product_group"),
            pg_opts,
            key="dm_pg_filter",
        )

    with col_demo_channel:
        target_ch_dm = st.selectbox(
            t("channel"),
            ch_opts,
            key="dm_ch_filter",
        )

    # 선택된 Product Group × Channel 범위에서 상품 목록 생성
    product_options = ["All"]

    if "PRODUCT" in df_mpf_curr_conv.columns:
        product_scope = filter_data(
            df_mpf_curr_conv,
            target_pg_dm,
            target_ch_dm,
        )

        product_options += sorted(
            product_scope[
                "PRODUCT"
            ].dropna().unique().tolist()
        )

    with col_demo_product:
        target_prod_dm = st.selectbox(
            t("product"),
            product_options,
            key=(
                f"dm_prod_filter_"
                f"{target_pg_dm}_"
                f"{target_ch_dm}"
            ),
        )

    # ════════════════════════════════════════════════════════════
    # 2. 선택 범위 데이터
    # ════════════════════════════════════════════════════════════
    vnb_dm = cached_filtered_walk(
        df_vnb_prev_full_raw,
        df_vnb_curr_full_raw,
        df_vnb_res_raw,
        year,
        quarter,
        target_ch_dm,
        target_pg_dm,
        fx_rate,
        display_currency,
        product=target_prod_dm,
    )

    curr_dm = filter_data(
        df_mpf_curr_conv,
        target_pg_dm,
        target_ch_dm,
        target_prod=target_prod_dm,
    )

    prev_dm = filter_data(
        df_mpf_prev_conv,
        target_pg_dm,
        target_ch_dm,
        target_prod=target_prod_dm,
    )

    if target_prod_dm == "All":
        scope_title = (
            f"{target_pg_dm} × "
            f"{target_ch_dm}"
        )
    else:
        scope_title = (
            f"{target_pg_dm} × "
            f"{target_ch_dm} × "
            f"{target_prod_dm}"
        )

    # ════════════════════════════════════════════════════════════
    # 3. VNB Walk
    # ════════════════════════════════════════════════════════════
    waterfall_title = t(
        "vnb_walk_scope",
        scope=scope_title,
    )

    fig_demo_waterfall = create_waterfall_chart(
        vnb_dm,
        waterfall_title,
        step_order,
        display_currency,
        fx_unit_suffix,
        ct_pq_anp=ct_pq_anp,
        ct_cq_anp=ct_cq_anp,
        language=language,
    )

    st.plotly_chart(
        fig_demo_waterfall,
        width="stretch",
        key="dm_waterfall",
    )

    html_report.add_plotly(
        waterfall_title,
        fig_demo_waterfall,
        description=unit_label,
    )

    step_detail = render_step_detail_table(
        vnb_dm,
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

    st.divider()

    st.caption(
        t("demo_note")
    )

    # ════════════════════════════════════════════════════════════
    # 4. Product Mix
    # ════════════════════════════════════════════════════════════
    mix_column = (
        "PRODUCT_ITEM"
        if "PRODUCT_ITEM" in prev_dm.columns
        else (
            "PROD_NAME_MP"
            if "PROD_NAME_MP" in prev_dm.columns
            else "PRODUCT"
        )
    )

    product_mix_previous = (
        get_dim_mix(
            prev_dm,
            mix_column,
        )
        .rename(
            columns={
                "Mix(%)": "Prev. Mix(%)",
            }
        )
    )

    product_mix_current = (
        get_dim_mix(
            curr_dm,
            mix_column,
        )
        .rename(
            columns={
                "Mix(%)": "Curr. Mix(%)",
            }
        )
    )

    product_comparison = pd.merge(
        product_mix_previous[
            [
                mix_column,
                "Prev. Mix(%)",
            ]
        ],
        product_mix_current[
            [
                mix_column,
                "Curr. Mix(%)",
            ]
        ],
        on=mix_column,
        how="outer",
    ).fillna(0).infer_objects(copy=False)

    product_comparison["Diff(%p)"] = (
        product_comparison["Curr. Mix(%)"]
        - product_comparison["Prev. Mix(%)"]
    )

    product_comparison_sorted = product_comparison.reindex(
        product_comparison["Diff(%p)"]
        .abs()
        .sort_values(ascending=False)
        .index
    ).reset_index(drop=True)

    with st.expander(
        t("detailed_product_mix"),
        expanded=False,
    ):
        if (
            show_charts
            and not product_comparison_sorted.empty
        ):
            fig_demo_product_mix = product_mix_diff_bar(
                product_comparison_sorted,
                mix_column,
                top_n=15,
                language=language,
            )

            st.plotly_chart(
                fig_demo_product_mix,
                width="stretch",
                key="demo_prod_mix_diff",
            )

            st.caption(
                t("top_15_product_note")
            )

            html_report.add_plotly(
                (
                    "Detailed Product Mix — Top 15 Changes"
                    if language == "English"
                    else "상세 상품 Mix — 변동 상위 15개"
                ),
                fig_demo_product_mix,
            )

        st.caption(
            t("top_four_highlight")
        )

        st.dataframe(
            product_comparison_sorted.style
            .format({
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
                    product_comparison_sorted,
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
            "Detailed Product Mix"
            if language == "English"
            else "상세 상품 Mix"
        ),
        product_comparison_sorted,
        index=False,
    )

    # ════════════════════════════════════════════════════════════
    # 5. Average Ticket Size
    # ════════════════════════════════════════════════════════════
    ticket_size_previous = (
        calc_ticket_size_v2(
            prev_dm
        )
        .rename(
            columns={
                "Ticket Size": "Prev. TS",
            }
        )
    )

    ticket_size_current = (
        calc_ticket_size_v2(
            curr_dm
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
        .replace(
            [
                np.inf,
                -np.inf,
            ],
            0,
        )
        .fillna(0)
        * 100
    )

    with st.expander(
        t("average_ticket_size"),
        expanded=False,
    ):
        st.caption(
            unit_label
        )

        st.dataframe(
            ticket_size_comparison.style
            .format({
                "Prev. TS": (
                    lambda value:
                    format_value(
                        value,
                        "amount",
                    )
                ),
                "Curr. TS": (
                    lambda value:
                    format_value(
                        value,
                        "amount",
                    )
                ),
                "Growth(%)": (
                    lambda value:
                    format_value(
                        value,
                        "percent",
                    )
                ),
            })
            .set_table_styles(
                th_center
            ),
            width="stretch",
        )

    html_report.add_dataframe(
        t("average_ticket_size"),
        ticket_size_comparison,
        description=unit_label,
        index=False,
    )

    # ════════════════════════════════════════════════════════════
    # 6. Premium Term Distribution
    # ════════════════════════════════════════════════════════════
    term_previous = (
        get_term_mix(
            prev_dm,
            other_limit,
        )[
            [
                "PREM_PERIOD",
                "Mix(%)",
            ]
        ]
        .rename(
            columns={
                "PREM_PERIOD": "Term",
                "Mix(%)": "Prev. Mix(%)",
            }
        )
    )

    term_current = (
        get_term_mix(
            curr_dm,
            other_limit,
        )[
            [
                "PREM_PERIOD",
                "Mix(%)",
            ]
        ]
        .rename(
            columns={
                "PREM_PERIOD": "Term",
                "Mix(%)": "Curr. Mix(%)",
            }
        )
    )

    term_comparison = safe_fillna(
        pd.merge(
            term_previous,
            term_current,
            on="Term",
            how="outer",
        )
    )

    term_comparison["Diff(%p)"] = (
        term_comparison["Curr. Mix(%)"]
        - term_comparison["Prev. Mix(%)"]
    )

    term_display = term_comparison[
        [
            "Term",
            "Prev. Mix(%)",
            "Curr. Mix(%)",
            "Diff(%p)",
        ]
    ].copy()

    with st.expander(
        t("premium_term_distribution"),
        expanded=False,
    ):
        if not term_comparison.empty:
            fig_term = term_compare_bar(
                term_comparison,
                language=language,
            )

            st.plotly_chart(
                fig_term,
                width="stretch",
                key="dm_term_bar",
            )

            html_report.add_plotly(
                t("premium_term_distribution"),
                fig_term,
            )

        st.dataframe(
            term_display.style
            .format({
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
        t("premium_term_distribution"),
        term_display,
        index=False,
    )

    # ════════════════════════════════════════════════════════════
    # 7. Age Group Distribution
    # ════════════════════════════════════════════════════════════
    age_previous = (
        get_age_group_mix(
            prev_dm
        )
        .rename(
            columns={
                "Mix(%)": "Prev. Mix(%)",
            }
        )
    )

    age_current = (
        get_age_group_mix(
            curr_dm
        )
        .rename(
            columns={
                "Mix(%)": "Curr. Mix(%)",
            }
        )
    )

    age_comparison = safe_fillna(
        pd.merge(
            age_previous[
                [
                    "Age Group",
                    "Prev. Mix(%)",
                ]
            ],
            age_current[
                [
                    "Age Group",
                    "Curr. Mix(%)",
                ]
            ],
            on="Age Group",
            how="outer",
        )
    )

    age_comparison["Diff(%p)"] = (
        age_comparison["Curr. Mix(%)"]
        - age_comparison["Prev. Mix(%)"]
    )

    with st.expander(
        t("age_group_distribution"),
        expanded=False,
    ):
        if not age_comparison.empty:
            fig_age = age_compare_bar(
                age_comparison,
                language=language,
            )

            st.plotly_chart(
                fig_age,
                width="stretch",
                key="dm_age_bar",
            )

            html_report.add_plotly(
                t("age_group_distribution"),
                fig_age,
            )

        st.dataframe(
            age_comparison.style
            .format({
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
        t("age_group_distribution"),
        age_comparison,
        index=False,
    )

    # ════════════════════════════════════════════════════════════
    # 8. Deferment Period
    # ════════════════════════════════════════════════════════════
    average_deferment_previous = get_defer_avg(
        prev_dm
    )

    average_deferment_current = get_defer_avg(
        curr_dm
    )

    deferment_comparison = pd.DataFrame()

    if "DEFER_Y" in curr_dm.columns:
        with st.expander(
            t("deferment_average"),
            expanded=False,
        ):
            if (
                average_deferment_current is not None
                or average_deferment_previous is not None
            ):
                defer_col_1, defer_col_2, defer_col_3 = st.columns(
                    3
                )

                defer_col_1.metric(
                    t("prev_avg_deferment"),
                    (
                        f"{average_deferment_previous:.2f}"
                        if average_deferment_previous is not None
                        else "N/A"
                    ),
                )

                defer_col_2.metric(
                    t("curr_avg_deferment"),
                    (
                        f"{average_deferment_current:.2f}"
                        if average_deferment_current is not None
                        else "N/A"
                    ),
                    delta=(
                        f"{average_deferment_current - average_deferment_previous:+.2f} yrs"
                        if (
                            average_deferment_current is not None
                            and average_deferment_previous is not None
                        )
                        else None
                    ),
                )

                st.caption(
                    t("deferment_exclusion_note")
                )

                if show_charts:
                    previous_non_zero = (
                        prev_dm[
                            prev_dm["DEFER_Y"] > 0
                        ]
                        if not prev_dm.empty
                        else prev_dm
                    )

                    current_non_zero = (
                        curr_dm[
                            curr_dm["DEFER_Y"] > 0
                        ]
                        if not curr_dm.empty
                        else curr_dm
                    )

                    deferment_previous = (
                        get_defer_mix(
                            previous_non_zero,
                            1.0,
                        )[
                            [
                                "DEFER_Y",
                                "Mix(%)",
                            ]
                        ]
                        .rename(
                            columns={
                                "Mix(%)": "Prev. Mix(%)",
                            }
                        )
                    )

                    deferment_current = (
                        get_defer_mix(
                            current_non_zero,
                            1.0,
                        )[
                            [
                                "DEFER_Y",
                                "Mix(%)",
                            ]
                        ]
                        .rename(
                            columns={
                                "Mix(%)": "Curr. Mix(%)",
                            }
                        )
                    )

                    deferment_comparison = safe_fillna(
                        pd.merge(
                            deferment_previous,
                            deferment_current,
                            on="DEFER_Y",
                            how="outer",
                        )
                    )

                    if not deferment_comparison.empty:
                        deferment_title = (
                            "Deferment Period Distribution "
                            "(DEFER_Y > 0) · Previous vs Current"
                            if language == "English"
                            else
                            "거치기간 분포 "
                            "(DEFER_Y > 0) · 전분기 vs 당분기"
                        )

                        fig_deferment = defer_compare_bar(
                            deferment_comparison,
                            deferment_title,
                            language=language,
                        )

                        st.plotly_chart(
                            fig_deferment,
                            width="stretch",
                            key="dm_defer_bar",
                        )

                        html_report.add_plotly(
                            (
                                "Deferment Period Distribution"
                                if language == "English"
                                else "거치기간 분포"
                            ),
                            fig_deferment,
                        )

                        html_report.add_dataframe(
                            (
                                "Deferment Period Distribution"
                                if language == "English"
                                else "거치기간 분포"
                            ),
                            deferment_comparison,
                            index=False,
                        )

            else:
                st.info(
                    t("no_deferment_contracts")
                )

    # HTML Export용 평균 거치기간 KPI
    if (
        average_deferment_current is not None
        or average_deferment_previous is not None
    ):
        deferment_items = [
            (
                t("prev_avg_deferment"),
                (
                    f"{average_deferment_previous:.2f}"
                    if average_deferment_previous is not None
                    else "N/A"
                ),
                None,
            ),
            (
                t("curr_avg_deferment"),
                (
                    f"{average_deferment_current:.2f}"
                    if average_deferment_current is not None
                    else "N/A"
                ),
                (
                    f"{average_deferment_current - average_deferment_previous:+.2f} yrs"
                    if (
                        average_deferment_current is not None
                        and average_deferment_previous is not None
                    )
                    else None
                ),
            ),
        ]

        html_report.add_kpis(
            t("deferment_average"),
            deferment_items,
        )

    # ════════════════════════════════════════════════════════════
    # 9. Analysis Report
    # ════════════════════════════════════════════════════════════
    st.divider()

    st.subheader(
        t("analysis_report")
    )

    demo_draft = generate_demo_draft(
        target_pg_dm,
        target_ch_dm,
        product_comparison_sorted,
        ticket_size_comparison,
        term_comparison,
        age_comparison,
        display_currency,
        mix_threshold=1.0,
        avg_defer_prev=average_deferment_previous,
        avg_defer_curr=average_deferment_current,
        language=language,
    )

    final_analysis = render_note_section(
        tab_name="Demo",
        keys=[
            target_pg_dm,
            target_ch_dm,
            target_prod_dm,
        ],
        NOTES_FILE=notes_file,
        auto_draft=demo_draft,
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
        description=scope_title,
    )