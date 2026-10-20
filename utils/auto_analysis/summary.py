"""
utils/auto_analysis/summary.py
──────────────────────────────
Summary 탭 자동 분석 초안 생성.

분석 범위
---------
1. Executive Summary
2. ANP Analysis
3. VNB Amount Analysis
4. Margin Analysis
5. Walk Step Drivers
6. Overall Assessment
7. Top Drivers

Korean / English Markdown 분석 보고서를 생성한다.
"""

from __future__ import annotations

import pandas as pd

from ._common import (
    _fmt_amt,
    _fmt_pct,
    _is_english,
    _trend_word,
)


def generate_summary_draft(
    df_vnb_walk: pd.DataFrame,
    comp_table: pd.DataFrame,
    pg_table: pd.DataFrame,
    display_currency: str,
    step_order: list,
    ch_mix_comp: pd.DataFrame | None = None,
    prod_mix_comp: pd.DataFrame | None = None,
    ts_comp: pd.DataFrame | None = None,
    age_comp: pd.DataFrame | None = None,
    term_comp: pd.DataFrame | None = None,
    economic_info: dict | None = None,
    comm_comp: pd.DataFrame | None = None,
    expense_info: dict | None = None,
    language: str = "Korean",
) -> str:
    """
    Company Total Summary 자동 분석 초안을 생성한다.

    Parameters
    ----------
    df_vnb_walk:
        Company Total VNB Walk DataFrame.

    comp_table:
        채널별 Summary MultiIndex DataFrame.

    pg_table:
        상품군별 Summary MultiIndex DataFrame.

    display_currency:
        KRW 또는 USD.

    step_order:
        VNB Walk Step 순서.

    language:
        Korean 또는 English.

    Notes
    -----
    나머지 선택 인수는 기존 호출부와의 호환성을 위해 유지한다.
    """
    del ch_mix_comp
    del prod_mix_comp
    del ts_comp
    del age_comp
    del term_comp
    del comm_comp
    del expense_info

    is_english = _is_english(language)

    lines: list[str] = []

    lines.append(
        (
            "## 📊 Company Total VNB Walk – Automated Analysis\n"
            if is_english
            else "## 📊 Company Total VNB Walk – 자동 분석\n"
        )
    )

    # ════════════════════════════════════════════════════════════
    # 내부 헬퍼
    # ════════════════════════════════════════════════════════════
    def trend_emoji(
        difference: float,
        threshold: float = 0.0,
    ) -> str:
        """증감 방향에 따른 아이콘을 반환한다."""
        if difference > threshold:
            return "📈"

        if difference < -threshold:
            return "📉"

        return "→"

    def top_n(
        dataframe: pd.DataFrame,
        column,
        number: int = 3,
    ) -> pd.DataFrame:
        """지정 열 기준 상위 N개 행을 반환한다."""
        if (
            dataframe.empty
            or column not in dataframe.columns
        ):
            return dataframe.head(0)

        return dataframe.sort_values(
            column,
            ascending=False,
        ).head(number)

    def mix_rows(
        rows: pd.DataFrame,
        total_previous: float,
        total_current: float,
    ) -> list:
        """ANP 비중과 현재 Margin을 계산한다."""
        previous_denominator = (
            total_previous
            if total_previous
            else 1.0
        )

        current_denominator = (
            total_current
            if total_current
            else 1.0
        )

        output: list[dict] = []

        for row_name, row in rows.iterrows():
            previous_share = (
                float(row[("PREV", "ANP")])
                / previous_denominator
                * 100
            )

            current_share = (
                float(row[("CURR", "ANP")])
                / current_denominator
                * 100
            )

            output.append({
                "name": str(row_name),
                "anp_current": float(
                    row[("CURR", "ANP")]
                ),
                "share_previous": previous_share,
                "share_current": current_share,
                "mix_difference": (
                    current_share
                    - previous_share
                ),
                "margin_current": float(
                    row[("CURR", "VNB%")]
                ),
            })

        return output

    def weighted_average_margin(
        selected_rows: list[dict],
    ) -> float:
        """Mix 변동폭을 가중치로 사용해 Margin 평균을 계산한다."""
        total_weight = sum(
            abs(row["mix_difference"])
            for row in selected_rows
        )

        if not total_weight:
            return 0.0

        return sum(
            row["margin_current"]
            * abs(row["mix_difference"])
            for row in selected_rows
        ) / total_weight

    def mix_narrative(
        calculated_mix_rows: list[dict],
        korean_label: str,
        english_label: str,
    ) -> str:
        """Mix 확대/축소 그룹의 Margin을 비교한다."""
        gainers = sorted(
            [
                row
                for row in calculated_mix_rows
                if row["mix_difference"] > 0.1
            ],
            key=lambda row: abs(
                row["mix_difference"]
            ),
            reverse=True,
        )

        losers = sorted(
            [
                row
                for row in calculated_mix_rows
                if row["mix_difference"] < -0.1
            ],
            key=lambda row: abs(
                row["mix_difference"]
            ),
            reverse=True,
        )

        label = (
            english_label
            if is_english
            else korean_label
        )

        if gainers and losers:
            gainer_margin = weighted_average_margin(
                gainers
            )

            loser_margin = weighted_average_margin(
                losers
            )

            gainer_names = ", ".join(
                row["name"]
                for row in gainers[:2]
            )

            loser_names = ", ".join(
                row["name"]
                for row in losers[:2]
            )

            if gainer_margin > loser_margin:
                if is_english:
                    impact = "a positive Margin Mix impact"
                    relationship = "higher than"
                else:
                    impact = "Margin 개선 요인"
                    relationship = "높습니다"

            elif gainer_margin < loser_margin:
                if is_english:
                    impact = "a negative Margin Mix impact"
                    relationship = "lower than"
                else:
                    impact = "Margin 하락 요인"
                    relationship = "낮습니다"

            else:
                if is_english:
                    impact = "a broadly neutral Margin Mix impact"
                    relationship = "in line with"
                else:
                    impact = "Margin 중립 요인"
                    relationship = "유사합니다"

            if is_english:
                return (
                    f"The weighted-average Margin of the {label} with "
                    f"increased Mix ({gainer_names}) was "
                    f"{gainer_margin:.2f}%, which was {relationship} "
                    f"the {loser_margin:.2f}% Margin of the {label} with "
                    f"decreased Mix ({loser_names}). The Mix movement had "
                    f"**{impact}**."
                )

            return (
                f"비중이 확대된 {label}({gainer_names})의 가중평균 Margin은 "
                f"{gainer_margin:.2f}%로, 비중이 축소된 "
                f"{label}({loser_names})의 {loser_margin:.2f}%보다 "
                f"{relationship}. 해당 Mix 변화는 **{impact}**으로 작용했습니다."
            )

        if gainers:
            gainer_margin = weighted_average_margin(
                gainers
            )

            gainer_names = ", ".join(
                row["name"]
                for row in gainers[:2]
            )

            if is_english:
                return (
                    f"The {label} with increased Mix were {gainer_names}, "
                    f"with a weighted-average Margin of "
                    f"{gainer_margin:.2f}%."
                )

            return (
                f"비중이 확대된 {label}은 {gainer_names}이며, "
                f"가중평균 Margin은 {gainer_margin:.2f}%입니다."
            )

        if losers:
            loser_margin = weighted_average_margin(
                losers
            )

            loser_names = ", ".join(
                row["name"]
                for row in losers[:2]
            )

            if is_english:
                return (
                    f"The {label} with decreased Mix were {loser_names}, "
                    f"with a weighted-average Margin of "
                    f"{loser_margin:.2f}%."
                )

            return (
                f"비중이 축소된 {label}은 {loser_names}이며, "
                f"가중평균 Margin은 {loser_margin:.2f}%입니다."
            )

        if is_english:
            return (
                f"The {label} Mix movement was limited to within ±0.1%p."
            )

        return (
            f"{label} 비중 변동은 ±0.1%p 이내로 크지 않았습니다."
        )

    # ════════════════════════════════════════════════════════════
    # 공통 데이터 추출
    # ════════════════════════════════════════════════════════════
    has_total = (
        "TOTAL (Company)"
        in comp_table.index
    )

    excluded_rows = {
        "TOTAL (Company)",
        "Non-Model",
    }

    channel_rows = comp_table.drop(
        index=[
            row_name
            for row_name in excluded_rows
            if row_name in comp_table.index
        ],
        errors="ignore",
    )

    product_group_rows = pg_table.drop(
        index=[
            row_name
            for row_name in excluded_rows
            if row_name in pg_table.index
        ],
        errors="ignore",
    )

    # VNB Walk Step Delta 계산
    step_deltas: dict[str, float] = {}

    if (
        not df_vnb_walk.empty
        and "STEP" in df_vnb_walk.columns
        and "VNB" in df_vnb_walk.columns
    ):
        step_vnb = (
            df_vnb_walk
            .groupby("STEP")["VNB"]
            .sum()
            .reindex(step_order)
            .fillna(0)
        )

        previous_value = 0.0

        for step in step_order:
            step_value = float(
                step_vnb.get(
                    step,
                    0.0,
                )
            )

            if step == "PQ":
                previous_value = step_value
                continue

            if step == "CQ":
                continue

            step_deltas[step] = (
                step_value
                - previous_value
            )

            previous_value = step_value

    # Company Total 지표
    if has_total:
        total_row = comp_table.loc[
            "TOTAL (Company)"
        ]

        anp_previous = float(
            total_row[("PREV", "ANP")]
        )

        anp_current = float(
            total_row[("CURR", "ANP")]
        )

        anp_difference = float(
            total_row[("DIFF", "ANP")]
        )

        vnb_previous = float(
            total_row[("PREV", "VNB")]
        )

        vnb_current = float(
            total_row[("CURR", "VNB")]
        )

        vnb_difference = float(
            total_row[("DIFF", "VNB")]
        )

        margin_previous = float(
            total_row[("PREV", "VNB%")]
        )

        margin_current = float(
            total_row[("CURR", "VNB%")]
        )

        margin_difference = float(
            total_row[("DIFF", "VNB%")]
        )

        anp_growth = (
            anp_difference
            / anp_previous
            * 100
            if anp_previous
            else 0.0
        )

        vnb_growth = (
            vnb_difference
            / vnb_previous
            * 100
            if vnb_previous
            else 0.0
        )

    else:
        anp_previous = 0.0
        anp_current = 0.0
        anp_difference = 0.0
        vnb_previous = 0.0
        vnb_current = 0.0
        vnb_difference = 0.0
        margin_previous = 0.0
        margin_current = 0.0
        margin_difference = 0.0
        anp_growth = 0.0
        vnb_growth = 0.0

    # 채널 및 상품군 Mix
    required_summary_columns = {
        ("PREV", "ANP"),
        ("CURR", "ANP"),
        ("CURR", "VNB%"),
    }

    if (
        not channel_rows.empty
        and required_summary_columns.issubset(
            channel_rows.columns
        )
    ):
        channel_mix = mix_rows(
            channel_rows,
            anp_previous,
            anp_current,
        )
    else:
        channel_mix = []

    if (
        not product_group_rows.empty
        and required_summary_columns.issubset(
            product_group_rows.columns
        )
    ):
        product_group_mix = mix_rows(
            product_group_rows,
            anp_previous,
            anp_current,
        )
    else:
        product_group_mix = []

    # Net Walk Impact
    net_tvog = (
        step_deltas.get(
            "PQ_TVOG",
            0.0,
        )
        + step_deltas.get(
            "CQ_TVOG",
            0.0,
        )
    )

    net_etu = (
        step_deltas.get(
            "PQ_ETU",
            0.0,
        )
        + step_deltas.get(
            "OTH_ETU",
            0.0,
        )
    )

    net_commission = (
        step_deltas.get(
            "PQ_COMM",
            0.0,
        )
        + step_deltas.get(
            "OTH_COMM",
            0.0,
        )
    )

    sales_volume_impact = step_deltas.get(
        "SL_VOL",
        0.0,
    )

    sales_mix_impact = step_deltas.get(
        "SL_MIX",
        0.0,
    )

    sales_demo_impact = step_deltas.get(
        "SL_DEMO",
        0.0,
    )

    economic_nmr_impact = step_deltas.get(
        "EC_NMR",
        0.0,
    )

    economic_fx_impact = step_deltas.get(
        "EC_FX",
        0.0,
    )

    net_component_steps = {
        "PQ_TVOG",
        "CQ_TVOG",
        "PQ_ETU",
        "OTH_ETU",
        "PQ_COMM",
        "OTH_COMM",
    }

    all_step_impacts: dict[str, float] = {
        "NET_TVOG": net_tvog,
        "NET_ETU": net_etu,
        "NET_COMM": net_commission,
    }

    for step_name, step_value in step_deltas.items():
        if step_name in net_component_steps:
            continue

        all_step_impacts[
            step_name
        ] = step_value

    sorted_impacts = sorted(
        all_step_impacts.items(),
        key=lambda item: abs(item[1]),
        reverse=True,
    )

    # ════════════════════════════════════════════════════════════
    # 1. Executive Summary
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 1) Executive Summary"
        if is_english
        else "### 1) Executive Summary"
    )

    if has_total:
        if (
            anp_difference > 0
            and vnb_difference > 0
            and margin_difference > 0
        ):
            headline = (
                "The quarter delivered both new-business volume growth "
                "and Margin improvement."
                if is_english
                else "신계약 볼륨 성장과 Margin 개선이 동시에 달성된 분기입니다."
            )

        elif (
            anp_difference > 0
            and vnb_difference > 0
            and margin_difference <= 0
        ):
            headline = (
                "VNB increased through volume growth, although Margin contracted."
                if is_english
                else "볼륨 성장으로 VNB가 증가했으나 Margin은 축소된 분기입니다."
            )

        elif (
            anp_difference > 0
            and vnb_difference <= 0
        ):
            headline = (
                "VNB decreased despite volume growth because of Margin pressure."
                if is_english
                else "볼륨 성장에도 Margin 하락 영향으로 VNB가 감소한 분기입니다."
            )

        elif (
            anp_difference <= 0
            and vnb_difference > 0
        ):
            headline = (
                "VNB increased despite lower volume, supported by Margin improvement."
                if is_english
                else "볼륨 감소에도 Margin 개선에 힘입어 VNB가 증가한 분기입니다."
            )

        else:
            headline = (
                "Both new-business volume and profitability weakened "
                "from the previous quarter."
                if is_english
                else "신계약 볼륨과 수익성이 모두 전분기 대비 약화된 분기입니다."
            )

        lines.append(headline)

        if is_english:
            lines.append(
                f"- ANP: **{_fmt_amt(anp_current, display_currency)}** "
                f"({trend_emoji(anp_difference)} {anp_growth:+.1f}% vs Previous Quarter)"
            )

            lines.append(
                f"- VNB: **{_fmt_amt(vnb_current, display_currency)}** "
                f"({trend_emoji(vnb_difference)} {vnb_growth:+.1f}% vs Previous Quarter)"
            )

            lines.append(
                f"- Margin: **{_fmt_pct(margin_current)}** "
                f"({trend_emoji(margin_difference)} "
                f"{_fmt_pct(margin_difference, with_sign=True, suffix='%p')})"
            )

        else:
            lines.append(
                f"- ANP: **{_fmt_amt(anp_current, display_currency)}** "
                f"({trend_emoji(anp_difference)} 전분기 대비 {anp_growth:+.1f}%)"
            )

            lines.append(
                f"- VNB: **{_fmt_amt(vnb_current, display_currency)}** "
                f"({trend_emoji(vnb_difference)} 전분기 대비 {vnb_growth:+.1f}%)"
            )

            lines.append(
                f"- Margin: **{_fmt_pct(margin_current)}** "
                f"({trend_emoji(margin_difference)} "
                f"{_fmt_pct(margin_difference, with_sign=True, suffix='%p')})"
            )

        top_impacts = [
            (
                step_name,
                step_value,
            )
            for step_name, step_value in sorted_impacts
            if abs(step_value) > 0
        ][:2]

        if top_impacts:
            top_impact_text = ", ".join(
                (
                    f"{step_name} "
                    f"{_fmt_amt(step_value, display_currency)}"
                )
                for step_name, step_value in top_impacts
            )

            lines.append(
                (
                    f"- Key Walk drivers: {top_impact_text}"
                    if is_english
                    else f"- 주요 Walk 동인: {top_impact_text}"
                )
            )

    else:
        lines.append(
            "- Company Total summary data is not available."
            if is_english
            else "- Company Total Summary 데이터가 없습니다."
        )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 2. ANP Analysis
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 2) ANP Analysis"
        if is_english
        else "### 2) ANP 분석"
    )

    if has_total:
        if is_english:
            lines.append(
                f"Company Total ANP was "
                f"**{_fmt_amt(anp_current, display_currency)}**, a change of "
                f"**{anp_growth:+.1f}%** or "
                f"**{_fmt_amt(anp_difference, display_currency)}** "
                f"from the previous quarter."
            )
        else:
            lines.append(
                f"전사 ANP는 **{_fmt_amt(anp_current, display_currency)}**로, "
                f"전분기 대비 **{anp_growth:+.1f}%**, "
                f"**{_fmt_amt(anp_difference, display_currency)}** 변동했습니다."
            )

        if channel_mix:
            lines.append(
                "\n**ANP and Mix by Channel:**"
                if is_english
                else "\n**채널별 ANP 및 비중(Mix) 변동:**"
            )

            sorted_channel_mix = sorted(
                channel_mix,
                key=lambda row: row["anp_current"],
                reverse=True,
            )

            for row in sorted_channel_mix:
                trend = _trend_word(
                    row["mix_difference"],
                    language=language,
                )

                lines.append(
                    f"- **{row['name']}** "
                    f"(Margin {_fmt_pct(row['margin_current'])}): "
                    f"{_fmt_amt(row['anp_current'], display_currency)}, "
                    f"Mix {row['share_previous']:.1f}% → "
                    f"{row['share_current']:.1f}% "
                    f"({_fmt_pct(row['mix_difference'], with_sign=True, suffix='%p')} "
                    f"{trend})"
                )

            top_channel_mix = sorted(
                channel_mix,
                key=lambda row: abs(
                    row["mix_difference"]
                ),
                reverse=True,
            )[:3]

            if top_channel_mix:
                lines.append(
                    "\n**Top 3 Channel Mix Changes:**"
                    if is_english
                    else "\n**채널 비중 변동 Top 3:**"
                )

                for rank, row in enumerate(
                    top_channel_mix,
                    1,
                ):
                    lines.append(
                        f"{rank}. **{row['name']}**: "
                        f"{_fmt_pct(row['mix_difference'], with_sign=True, suffix='%p')}, "
                        f"Margin {_fmt_pct(row['margin_current'])}"
                    )

            lines.append(
                "\n"
                + mix_narrative(
                    channel_mix,
                    "채널",
                    "channels",
                )
            )

        if product_group_mix:
            lines.append(
                "\n**ANP and Mix by Product Group:**"
                if is_english
                else "\n**상품군별 ANP 및 비중(Mix) 변동:**"
            )

            sorted_product_group_mix = sorted(
                product_group_mix,
                key=lambda row: row["anp_current"],
                reverse=True,
            )

            for row in sorted_product_group_mix[:5]:
                trend = _trend_word(
                    row["mix_difference"],
                    language=language,
                )

                lines.append(
                    f"- **{row['name']}** "
                    f"(Margin {_fmt_pct(row['margin_current'])}): "
                    f"{_fmt_amt(row['anp_current'], display_currency)}, "
                    f"Mix {row['share_previous']:.1f}% → "
                    f"{row['share_current']:.1f}% "
                    f"({_fmt_pct(row['mix_difference'], with_sign=True, suffix='%p')} "
                    f"{trend})"
                )

            top_product_group_mix = sorted(
                product_group_mix,
                key=lambda row: abs(
                    row["mix_difference"]
                ),
                reverse=True,
            )[:3]

            if top_product_group_mix:
                lines.append(
                    "\n**Top 3 Product Group Mix Changes:**"
                    if is_english
                    else "\n**상품군 비중 변동 Top 3:**"
                )

                for rank, row in enumerate(
                    top_product_group_mix,
                    1,
                ):
                    lines.append(
                        f"{rank}. **{row['name']}**: "
                        f"{_fmt_pct(row['mix_difference'], with_sign=True, suffix='%p')}, "
                        f"Margin {_fmt_pct(row['margin_current'])}"
                    )

            lines.append(
                "\n"
                + mix_narrative(
                    product_group_mix,
                    "상품군",
                    "product groups",
                )
            )

        if (
            sales_volume_impact
            or sales_mix_impact
            or sales_demo_impact
        ):
            lines.append(
                "\n**Volume and Mix Walk Steps:**"
                if is_english
                else "\n**Volume 및 Mix Walk Step:**"
            )

            if sales_volume_impact:
                lines.append(
                    (
                        f"- **SL_VOL** {_fmt_amt(sales_volume_impact, display_currency)}: "
                        f"Impact from the change in new-business volume."
                        if is_english
                        else
                        f"- **SL_VOL** {_fmt_amt(sales_volume_impact, display_currency)}: "
                        f"신계약 볼륨 변화 영향입니다."
                    )
                )

            if sales_mix_impact:
                if product_group_mix:
                    largest_shift = max(
                        product_group_mix,
                        key=lambda row: abs(
                            row["mix_difference"]
                        ),
                    )

                    lines.append(
                        (
                            f"- **SL_MIX** {_fmt_amt(sales_mix_impact, display_currency)}: "
                            f"Channel, Product Group and Contract Type Mix changes. "
                            f"The largest Product Group Mix movement was "
                            f"**{largest_shift['name']}** at "
                            f"{_fmt_pct(largest_shift['mix_difference'], with_sign=True, suffix='%p')}, "
                            f"with a current Margin of "
                            f"{_fmt_pct(largest_shift['margin_current'])}."
                            if is_english
                            else
                            f"- **SL_MIX** {_fmt_amt(sales_mix_impact, display_currency)}: "
                            f"채널, 상품군 및 Contract Type Mix 변화 영향입니다. "
                            f"가장 큰 상품군 비중 변동은 "
                            f"**{largest_shift['name']}**의 "
                            f"{_fmt_pct(largest_shift['mix_difference'], with_sign=True, suffix='%p')}이며, "
                            f"당분기 Margin은 "
                            f"{_fmt_pct(largest_shift['margin_current'])}입니다."
                        )
                    )

                else:
                    lines.append(
                        (
                            f"- **SL_MIX** {_fmt_amt(sales_mix_impact, display_currency)}: "
                            f"Impact from Channel, Product Group and Contract Type Mix changes."
                            if is_english
                            else
                            f"- **SL_MIX** {_fmt_amt(sales_mix_impact, display_currency)}: "
                            f"채널, 상품군 및 Contract Type Mix 변화 영향입니다."
                        )
                    )

            if sales_demo_impact:
                lines.append(
                    (
                        f"- **SL_DEMO** {_fmt_amt(sales_demo_impact, display_currency)}: "
                        f"Product-level demographic and Mix impact."
                        if is_english
                        else
                        f"- **SL_DEMO** {_fmt_amt(sales_demo_impact, display_currency)}: "
                        f"상품 레벨 인구통계 및 Mix 차이 영향입니다."
                    )
                )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 3. VNB Amount Analysis
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 3) VNB Amount Analysis"
        if is_english
        else "### 3) VNB Amount 분석"
    )

    if has_total:
        if is_english:
            lines.append(
                f"Company Total VNB was "
                f"**{_fmt_amt(vnb_current, display_currency)}**, "
                f"a change of **{vnb_growth:+.1f}%** from the previous quarter. "
                f"The result reflects the combined effect of "
                f"{'higher' if anp_difference > 0 else 'lower'} ANP and "
                f"{'improved' if margin_difference > 0 else 'lower'} Margin."
            )
        else:
            lines.append(
                f"전사 VNB는 **{_fmt_amt(vnb_current, display_currency)}**로, "
                f"전분기 대비 **{vnb_growth:+.1f}%** 변동했습니다. "
                f"이는 ANP {'성장' if anp_difference > 0 else '감소'}과 "
                f"Margin {'확대' if margin_difference > 0 else '축소'}가 "
                f"결합된 결과입니다."
            )

        if (
            not channel_rows.empty
            and ("CURR", "VNB") in channel_rows.columns
        ):
            lines.append(
                "\n**VNB by Channel:**"
                if is_english
                else "\n**채널별 VNB:**"
            )

            sorted_channel_rows = channel_rows.sort_values(
                ("CURR", "VNB"),
                ascending=False,
            )

            for channel_name, row in sorted_channel_rows.iterrows():
                channel_vnb_difference = float(
                    row[("DIFF", "VNB")]
                )

                channel_margin_difference = float(
                    row[("DIFF", "VNB%")]
                )

                channel_anp_difference = float(
                    row[("DIFF", "ANP")]
                )

                channel_current_margin = float(
                    row[("CURR", "VNB%")]
                )

                if (
                    channel_anp_difference > 0
                    and channel_margin_difference > 0
                ):
                    cause = (
                        "Volume increased and Margin improved"
                        if is_english
                        else "볼륨 증가 + Margin 개선"
                    )

                elif (
                    channel_anp_difference > 0
                    and channel_margin_difference <= 0
                ):
                    cause = (
                        "Volume growth partly offset Margin pressure"
                        if is_english
                        else "볼륨 증가가 Margin 하락을 일부 보완"
                    )

                elif (
                    channel_anp_difference <= 0
                    and channel_margin_difference > 0
                ):
                    cause = (
                        "Margin improvement partly offset lower volume"
                        if is_english
                        else "Margin 개선이 볼륨 감소를 일부 보완"
                    )

                else:
                    cause = (
                        "Both volume and Margin declined"
                        if is_english
                        else "볼륨 감소 + Margin 하락"
                    )

                lines.append(
                    f"- **{channel_name}** "
                    f"(Margin {_fmt_pct(channel_current_margin)}, "
                    f"{_fmt_pct(channel_margin_difference, with_sign=True, suffix='%p')}): "
                    f"{_fmt_amt(float(row[('CURR', 'VNB')]), display_currency)}, "
                    f"change {_fmt_amt(channel_vnb_difference, display_currency)} "
                    f"[{cause}]"
                )

            top_vnb_channels = top_n(
                channel_rows,
                ("DIFF", "VNB"),
            )

            if not top_vnb_channels.empty:
                lines.append(
                    "\n**Top 3 Channels by VNB Change:**"
                    if is_english
                    else "\n**VNB 변화 Top 3 채널:**"
                )

                for rank, (
                    channel_name,
                    row,
                ) in enumerate(
                    top_vnb_channels.iterrows(),
                    1,
                ):
                    lines.append(
                        f"{rank}. **{channel_name}**: "
                        f"{_fmt_amt(float(row[('DIFF', 'VNB')]), display_currency)} "
                        f"(Margin "
                        f"{_fmt_pct(float(row[('DIFF', 'VNB%')]), with_sign=True, suffix='%p')})"
                    )

        if (
            not product_group_rows.empty
            and ("CURR", "VNB") in product_group_rows.columns
        ):
            top_vnb_product_groups = top_n(
                product_group_rows,
                ("CURR", "VNB"),
            )

            lines.append(
                "\n**Top 3 Product Groups by Current VNB:**"
                if is_english
                else "\n**VNB 규모 Top 3 상품군:**"
            )

            for rank, (
                product_group,
                row,
            ) in enumerate(
                top_vnb_product_groups.iterrows(),
                1,
            ):
                lines.append(
                    f"{rank}. **{product_group}**: "
                    f"{_fmt_amt(float(row[('CURR', 'VNB')]), display_currency)}, "
                    f"change {_fmt_amt(float(row[('DIFF', 'VNB')]), display_currency)}, "
                    f"Margin change "
                    f"{_fmt_pct(float(row[('DIFF', 'VNB%')]), with_sign=True, suffix='%p')}"
                )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 4. Margin Analysis
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 4) Margin Analysis"
        if is_english
        else "### 4) Margin 분석"
    )

    if has_total:
        margin_causes: list[str] = []

        if (
            abs(sales_mix_impact) > abs(economic_nmr_impact)
            and abs(sales_mix_impact) > abs(economic_fx_impact)
            and product_group_mix
        ):
            shifted_product_groups = sorted(
                product_group_mix,
                key=lambda row: abs(
                    row["mix_difference"]
                ),
                reverse=True,
            )[:2]

            shift_description = ", ".join(
                (
                    f"{row['name']} "
                    f"(Margin {_fmt_pct(row['margin_current'])})"
                )
                for row in shifted_product_groups
            )

            margin_causes.append(
                (
                    f"Product Group Mix changes, including {shift_description}"
                    if is_english
                    else f"{shift_description} 등 상품군 Mix 변화"
                )
            )

        if abs(economic_nmr_impact) > 1_000_000:
            margin_causes.append(
                (
                    f"Interest-rate and economic-assumption changes "
                    f"(EC_NMR {_fmt_amt(economic_nmr_impact, display_currency)})"
                    if is_english
                    else
                    f"금리 및 경제가정 변화 "
                    f"(EC_NMR {_fmt_amt(economic_nmr_impact, display_currency)})"
                )
            )

        if abs(economic_fx_impact) > 1_000_000:
            margin_causes.append(
                (
                    f"Foreign exchange movement "
                    f"(EC_FX {_fmt_amt(economic_fx_impact, display_currency)})"
                    if is_english
                    else
                    f"환율 변동 "
                    f"(EC_FX {_fmt_amt(economic_fx_impact, display_currency)})"
                )
            )

        if abs(net_commission) > 1_000_000:
            margin_causes.append(
                (
                    f"Commission changes "
                    f"(NET_COMM {_fmt_amt(net_commission, display_currency)})"
                    if is_english
                    else
                    f"수수료 변화 "
                    f"(NET_COMM {_fmt_amt(net_commission, display_currency)})"
                )
            )

        cause_text = (
            " / ".join(margin_causes)
            if margin_causes
            else (
                "multiple combined factors"
                if is_english
                else "복합 요인"
            )
        )

        if is_english:
            lines.append(
                f"Margin changed from "
                f"{_fmt_pct(margin_previous)} to "
                f"**{_fmt_pct(margin_current)}** "
                f"({_fmt_pct(margin_difference, with_sign=True, suffix='%p')}). "
                f"Key drivers were {cause_text}."
            )
        else:
            lines.append(
                f"Margin은 {_fmt_pct(margin_previous)}에서 "
                f"**{_fmt_pct(margin_current)}**로 변동했습니다 "
                f"({_fmt_pct(margin_difference, with_sign=True, suffix='%p')}). "
                f"주요 원인은 {cause_text}입니다."
            )

        if (
            not channel_rows.empty
            and ("CURR", "VNB%") in channel_rows.columns
        ):
            lines.append(
                "\n**Margin by Channel, Including ANP Mix:**"
                if is_english
                else "\n**채널별 Margin 및 ANP 비중:**"
            )

            sorted_margin_rows = channel_rows.sort_values(
                ("CURR", "VNB%"),
                ascending=False,
            )

            for channel_name, row in sorted_margin_rows.iterrows():
                channel_margin_difference = float(
                    row[("DIFF", "VNB%")]
                )

                channel_current_margin = float(
                    row[("CURR", "VNB%")]
                )

                channel_share = (
                    float(row[("CURR", "ANP")])
                    / (anp_current or 1)
                    * 100
                )

                channel_anp_difference = float(
                    row[("DIFF", "ANP")]
                )

                if (
                    channel_margin_difference < -0.5
                    and channel_anp_difference > 0
                ):
                    cross_comment = (
                        "Volume increased, but Margin declined"
                        if is_english
                        else "볼륨 증가에도 Margin 하락"
                    )

                elif (
                    channel_margin_difference > 0.5
                    and channel_anp_difference < 0
                ):
                    cross_comment = (
                        "Margin improved despite lower volume"
                        if is_english
                        else "볼륨 감소에도 Margin 개선"
                    )

                else:
                    cross_comment = ""

                lines.append(
                    f"- **{channel_name}** "
                    f"(ANP Mix {channel_share:.1f}%): "
                    f"{_fmt_pct(float(row[('PREV', 'VNB%')]))} → "
                    f"**{_fmt_pct(channel_current_margin)}** "
                    f"({_fmt_pct(channel_margin_difference, with_sign=True, suffix='%p')}) "
                    f"{cross_comment}"
                )

            top_margin_channels = top_n(
                channel_rows,
                ("DIFF", "VNB%"),
            )

            if not top_margin_channels.empty:
                lines.append(
                    "\n**Top 3 Channels by Margin Change:**"
                    if is_english
                    else "\n**Margin 변화 Top 3 채널:**"
                )

                for rank, (
                    channel_name,
                    row,
                ) in enumerate(
                    top_margin_channels.iterrows(),
                    1,
                ):
                    lines.append(
                        f"{rank}. **{channel_name}**: "
                        f"{_fmt_pct(float(row[('DIFF', 'VNB%')]), with_sign=True, suffix='%p')}"
                    )

        if (
            not product_group_rows.empty
            and ("CURR", "VNB%") in product_group_rows.columns
            and ("CURR", "ANP") in product_group_rows.columns
        ):
            top_product_groups_by_anp = product_group_rows.nlargest(
                3,
                ("CURR", "ANP"),
            )

            lines.append(
                "\n**Margin of Top 3 Product Groups by ANP:**"
                if is_english
                else "\n**ANP 상위 3개 상품군 Margin:**"
            )

            for product_group, row in top_product_groups_by_anp.iterrows():
                product_margin_difference = float(
                    row[("DIFF", "VNB%")]
                )

                product_current_margin = float(
                    row[("CURR", "VNB%")]
                )

                product_anp_difference = float(
                    row[("DIFF", "ANP")]
                )

                if (
                    product_margin_difference < -0.5
                    and product_anp_difference > 0
                ):
                    cross_comment = (
                        "Volume increased, but Margin declined; review Product Mix"
                        if is_english
                        else "볼륨 증가에도 Margin 하락; Product Mix 점검 필요"
                    )

                elif (
                    product_margin_difference > 0.5
                    and product_anp_difference < 0
                ):
                    cross_comment = (
                        "Margin improved despite lower volume"
                        if is_english
                        else "볼륨 감소에도 Margin 개선"
                    )

                else:
                    cross_comment = ""

                lines.append(
                    f"- **{product_group}**: "
                    f"{_fmt_pct(float(row[('PREV', 'VNB%')]))} → "
                    f"**{_fmt_pct(product_current_margin)}** "
                    f"({_fmt_pct(product_margin_difference, with_sign=True, suffix='%p')}) "
                    f"{cross_comment}"
                )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 5. Walk Step Drivers
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 5) Walk Step Drivers"
        if is_english
        else "### 5) Walk Step 인과"
    )

    if is_english:
        step_descriptions = {
            "NET_TVOG": (
                "Net TVOG impact, including the reversal of previous-quarter "
                "TVOG and the current-quarter recalculation"
            ),
            "NET_ETU": (
                "Net expense true-up impact from the difference between "
                "actual expenses and model assumptions"
            ),
            "NET_COMM": (
                "Net commission true-up impact from the difference between "
                "actual commission rates and Plan"
            ),
            "SL_VOL": "Change in new-business volume",
            "SL_MIX": "Channel, Product Group and Contract Type Mix changes",
            "SL_DEMO": "Product-level demographic and Mix differences",
            "EC_NMR": "Economic-assumption and interest-rate scenario changes",
            "EC_FX": "Foreign exchange movement",
            "MC": "Model change",
            "RP": "Repricing impact",
            "SL_NEW": "New-product impact",
        }
    else:
        step_descriptions = {
            "NET_TVOG": (
                "전분기 TVOG 차감과 당분기 TVOG 재산정을 포함한 "
                "TVOG Net 영향"
            ),
            "NET_ETU": (
                "Actual Expense와 Model 가정 차이에 따른 "
                "Expense True-up Net 영향"
            ),
            "NET_COMM": (
                "Actual Commission과 Plan 차이에 따른 "
                "Commission True-up Net 영향"
            ),
            "SL_VOL": "신계약 볼륨 변화 영향",
            "SL_MIX": "채널, 상품군 및 Contract Type Mix 변화 영향",
            "SL_DEMO": "상품 레벨 인구통계 및 Mix 차이",
            "EC_NMR": "금리 및 경제가정 시나리오 변화",
            "EC_FX": "환율 변화",
            "MC": "Model Change",
            "RP": "Repricing Impact",
            "SL_NEW": "신상품 영향",
        }

    lines.append(
        (
            "**Impact Ranking Based on Absolute VNB Movement:**"
            if is_english
            else "**VNB 금액 절대값 기준 Impact 순위:**"
        )
    )

    displayed_rank = 0

    for step_name, step_value in sorted_impacts:
        if abs(step_value) < 10_000:
            continue

        displayed_rank += 1

        if displayed_rank > 5:
            break

        description = step_descriptions.get(
            step_name,
            step_name,
        )

        extra_comment = ""

        if (
            step_name == "SL_MIX"
            and product_group_mix
        ):
            largest_shift = max(
                product_group_mix,
                key=lambda row: abs(
                    row["mix_difference"]
                ),
            )

            if is_english:
                extra_comment = (
                    f" The largest Product Group Mix movement was "
                    f"{largest_shift['name']} at "
                    f"{_fmt_pct(largest_shift['mix_difference'], with_sign=True, suffix='%p')}."
                )
            else:
                extra_comment = (
                    f" 가장 큰 상품군 Mix 변동은 "
                    f"{largest_shift['name']}의 "
                    f"{_fmt_pct(largest_shift['mix_difference'], with_sign=True, suffix='%p')}입니다."
                )

        elif (
            step_name == "EC_NMR"
            and not product_group_rows.empty
        ):
            rate_sensitive_groups = [
                product_group
                for product_group in product_group_rows.index
                if (
                    "annuity" in str(
                        product_group
                    ).lower()
                    or "연금" in str(
                        product_group
                    )
                )
            ]

            if rate_sensitive_groups:
                if is_english:
                    extra_comment = (
                        f" Review the exposure of rate-sensitive businesses "
                        f"such as {rate_sensitive_groups[0]}."
                    )
                else:
                    extra_comment = (
                        f" {rate_sensitive_groups[0]} 등 금리 민감 상품군의 "
                        f"영향을 함께 점검할 필요가 있습니다."
                    )

        elif step_name == "EC_FX":
            extra_comment = (
                " Review the Mix of USD-denominated business and exchange-rate movement."
                if is_english
                else " USD 계약 비중과 환율 변동을 함께 점검할 필요가 있습니다."
            )

        elif (
            step_name == "SL_VOL"
            and not channel_rows.empty
            and ("DIFF", "ANP") in channel_rows.columns
        ):
            if step_value > 0:
                channel_driver = channel_rows.sort_values(
                    ("DIFF", "ANP"),
                    ascending=False,
                ).index[0]

                extra_comment = (
                    f" The increase was mainly associated with higher volume "
                    f"in {channel_driver}."
                    if is_english
                    else f" {channel_driver} 등 주요 채널의 볼륨 증가와 연관됩니다."
                )

            else:
                channel_driver = channel_rows.sort_values(
                    ("DIFF", "ANP"),
                    ascending=True,
                ).index[0]

                extra_comment = (
                    f" The decrease was mainly associated with lower volume "
                    f"in {channel_driver}."
                    if is_english
                    else f" {channel_driver} 등 주요 채널의 볼륨 감소와 연관됩니다."
                )

        lines.append(
            f"{displayed_rank}. **{step_name}** "
            f"{_fmt_amt(step_value, display_currency)}: "
            f"{description}.{extra_comment}"
        )

    if displayed_rank == 0:
        lines.append(
            "- No material Walk Step impact was identified."
            if is_english
            else "- 유의미한 Walk Step 영향이 확인되지 않았습니다."
        )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 6. Overall Assessment
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 6) Overall Assessment"
        if is_english
        else "### 6) 종합 진단"
    )

    if has_total:
        if (
            anp_difference > 0
            and margin_difference > 0
        ):
            diagnosis = (
                f"ANP increased by {anp_growth:+.1f}% and Margin improved by "
                f"{_fmt_pct(margin_difference, with_sign=True, suffix='%p')}. "
                f"Both volume and profitability were favorable."
                if is_english
                else
                f"ANP는 {anp_growth:+.1f}% 증가하고 Margin은 "
                f"{_fmt_pct(margin_difference, with_sign=True, suffix='%p')} 개선되어, "
                f"볼륨과 수익성이 모두 우호적인 분기입니다."
            )

        elif (
            anp_difference > 0
            and margin_difference <= 0
        ):
            diagnosis = (
                f"ANP increased by {anp_growth:+.1f}%, but Margin declined by "
                f"{_fmt_pct(margin_difference, with_sign=True, suffix='%p')}. "
                f"Mix or economic-assumption changes placed pressure on profitability."
                if is_english
                else
                f"ANP는 {anp_growth:+.1f}% 증가했으나 Margin은 "
                f"{_fmt_pct(margin_difference, with_sign=True, suffix='%p')} 축소되었습니다. "
                f"Mix 또는 경제가정 변화가 수익성을 압박했습니다."
            )

        elif (
            anp_difference <= 0
            and vnb_difference > 0
        ):
            diagnosis = (
                "ANP declined, but Margin improvement supported higher VNB. "
                "This may indicate a shift toward more profitable new business."
                if is_english
                else
                "ANP는 감소했으나 Margin 개선으로 VNB가 증가했습니다. "
                "수익성 중심의 신계약 구조로 이동하고 있을 가능성이 있습니다."
            )

        else:
            diagnosis = (
                "Both ANP and VNB declined from the previous quarter, "
                "indicating simultaneous volume and profitability pressure."
                if is_english
                else
                "ANP와 VNB가 모두 전분기 대비 감소하여 "
                "볼륨과 수익성이 동시에 압박받고 있습니다."
            )

        lines.append(diagnosis)

        if (
            not channel_rows.empty
            and ("DIFF", "VNB") in channel_rows.columns
        ):
            best_channel = channel_rows.sort_values(
                ("DIFF", "VNB"),
                ascending=False,
            ).index[0]

            weakest_channel = channel_rows.sort_values(
                ("DIFF", "VNB"),
                ascending=True,
            ).index[0]

            if best_channel != weakest_channel:
                if is_english:
                    lines.append(
                        f"- Channel performance was differentiated: "
                        f"**{best_channel}** was the strongest contributor, "
                        f"while **{weakest_channel}** was the weakest."
                    )
                else:
                    lines.append(
                        f"- 채널별 실적 차이가 확인됩니다. "
                        f"**{best_channel}**이 가장 우호적인 기여를 보였고, "
                        f"**{weakest_channel}**이 가장 부진했습니다."
                    )

        if sorted_impacts:
            largest_step, largest_value = sorted_impacts[0]

            largest_description = step_descriptions.get(
                largest_step,
                largest_step,
            )

            if is_english:
                lines.append(
                    f"- The largest Walk impact was **{largest_step}** at "
                    f"**{_fmt_amt(largest_value, display_currency)}**: "
                    f"{largest_description}."
                )
            else:
                lines.append(
                    f"- 가장 큰 Walk 영향은 **{largest_step}**의 "
                    f"**{_fmt_amt(largest_value, display_currency)}**입니다: "
                    f"{largest_description}."
                )

        recommendations: list[str] = []

        if abs(sales_mix_impact) > abs(
            sales_volume_impact
        ) * 0.5:
            if (
                not product_group_rows.empty
                and ("DIFF", "VNB%")
                in product_group_rows.columns
            ):
                weakest_product_group = (
                    product_group_rows.sort_values(
                        ("DIFF", "VNB%")
                    ).index[0]
                )

                recommendations.append(
                    (
                        f"**Sales Mix tab**: Review the Mix movement of "
                        f"{weakest_product_group}."
                        if is_english
                        else
                        f"**Sales Mix 탭**: {weakest_product_group} 상품군의 "
                        f"Mix 변화를 상세 점검"
                    )
                )

        if (
            abs(economic_nmr_impact)
            > abs(sales_mix_impact) * 0.3
            or abs(economic_fx_impact)
            > abs(sales_mix_impact) * 0.3
        ):
            recommendations.append(
                (
                    "**Economic tab**: Compare interest-rate and foreign-exchange "
                    "scenarios with the previous quarter."
                    if is_english
                    else
                    "**Economic 탭**: 금리 및 환율 시나리오를 전분기와 비교"
                )
            )

        if (
            abs(net_commission)
            > abs(sales_volume_impact) * 0.2
        ):
            recommendations.append(
                (
                    "**Commission tab**: Review actual commission rates "
                    "against Plan."
                    if is_english
                    else
                    "**Commission 탭**: Actual Commission Rate의 "
                    "Plan 대비 편차 점검"
                )
            )

        if (
            abs(net_etu)
            > abs(sales_volume_impact) * 0.2
        ):
            recommendations.append(
                (
                    "**Expense tab**: Review ETU and the underlying expense structure."
                    if is_english
                    else
                    "**Expense 탭**: ETU 및 비용 구조 점검"
                )
            )

        if abs(sales_demo_impact) > 0:
            recommendations.append(
                (
                    "**Demo tab**: Review changes in age, premium term and Ticket Size."
                    if is_english
                    else
                    "**Demo 탭**: 연령, 납입기간 및 Ticket Size 구조 변화 점검"
                )
            )

        if recommendations:
            lines.append(
                "\n**Recommended Follow-up Analysis:**"
                if is_english
                else "\n**후속 분석 권장:**"
            )

            for recommendation in recommendations:
                lines.append(
                    f"- {recommendation}"
                )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 7. Top Drivers
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 7) Top 3 Drivers of Margin and VNB Change"
        if is_english
        else "### 7) Margin 및 VNB 변동 주요 요인 Top 3"
    )

    material_causes = [
        (
            step_name,
            step_value,
        )
        for step_name, step_value in all_step_impacts.items()
        if abs(step_value) > 10_000
    ]

    material_causes.sort(
        key=lambda item: abs(item[1]),
        reverse=True,
    )

    if material_causes:
        for rank, (
            step_name,
            step_value,
        ) in enumerate(
            material_causes[:3],
            1,
        ):
            lines.append(
                f"{rank}. **{step_name}**: "
                f"{_fmt_amt(step_value, display_currency)}"
            )

    else:
        lines.append(
            "- No material driver was identified."
            if is_english
            else "- 유의미한 변동 요인이 확인되지 않았습니다."
        )

    lines.append("")

    # Economic 정보가 별도로 전달된 경우 참고 정보 추가
    if economic_info:
        fx_change = economic_info.get(
            "fx_change",
            None,
        )

        rate_change = economic_info.get(
            "rate_change",
            None,
        )

        if (
            fx_change is not None
            or rate_change is not None
        ):
            lines.append(
                "### Appendix: Economic Indicators"
                if is_english
                else "### 참고: 경제지표"
            )

            if fx_change is not None:
                lines.append(
                    (
                        f"- Change in average FX rate: {float(fx_change):+,.1f} KRW/USD"
                        if is_english
                        else
                        f"- 평균 환율 변동: {float(fx_change):+,.1f} KRW/USD"
                    )
                )

            if rate_change is not None:
                lines.append(
                    (
                        f"- Interest-rate change: {float(rate_change):+,.1f} bps"
                        if is_english
                        else
                        f"- 금리 변동: {float(rate_change):+,.1f} bps"
                    )
                )

            lines.append("")

    return "\n".join(lines)