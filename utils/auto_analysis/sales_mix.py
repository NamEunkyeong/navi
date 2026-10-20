"""
utils/auto_analysis/sales_mix.py
────────────────────────────────
Sales Mix 탭 자동 분석 초안 생성.

분석 범위
---------
- VNB Walk 주요 변동
- Channel Mix
- Product Portfolio Mix
- Contract Type Mix
- 선택 범위 내 Margin과 Mix 변화 간 관계

Korean / English Markdown 분석 보고서를 생성한다.
"""

from __future__ import annotations

import pandas as pd

from utils.charts import compute_step_impacts

from ._common import (
    _fmt_amt,
    _fmt_pct,
    _is_english,
    _trend_word,
)


def generate_sales_mix_draft(
    target_pg: str,
    target_ch: str,
    ch_comp: pd.DataFrame,
    pg_comp: pd.DataFrame,
    vnb_walk_filtered: pd.DataFrame,
    display_currency: str,
    step_order: list,
    mix_threshold: float = 1.0,
    ct_comp: pd.DataFrame | None = None,
    comp_table: pd.DataFrame | None = None,
    pg_table: pd.DataFrame | None = None,
    ct_pq_anp: float = 0.0,
    ct_cq_anp: float = 0.0,
    language: str = "Korean",
) -> str:
    """
    Sales Mix 탭 자동 분석 초안을 생성한다.

    Parameters
    ----------
    target_pg:
        선택한 Product Group.

    target_ch:
        선택한 Channel.

    ch_comp:
        채널별 전분기/당분기 Mix 비교 DataFrame.

    pg_comp:
        상품별 전분기/당분기 Mix 비교 DataFrame.

    vnb_walk_filtered:
        선택 범위의 VNB Walk DataFrame.

    display_currency:
        KRW 또는 USD.

    step_order:
        VNB Walk Step 순서.

    mix_threshold:
        유의미한 Mix 변화로 판단할 Percentage Point 기준.

    ct_comp:
        Contract Type Mix 비교 DataFrame.

    comp_table:
        선택 상품군 범위의 채널별 Summary MultiIndex DataFrame.

    pg_table:
        선택 채널 범위의 상품군별 Summary MultiIndex DataFrame.

    ct_pq_anp:
        Company Total PQ ANP.

    ct_cq_anp:
        Company Total CQ ANP.

    language:
        Korean 또는 English.
    """
    is_english = _is_english(language)

    lines: list[str] = []

    scope = f"{target_pg} × {target_ch}"

    lines.append(
        (
            f"## 🧩 Sales Mix Analysis – {scope}\n"
            if is_english
            else f"## 🧩 Sales Mix 분석 – {scope}\n"
        )
    )

    # 분석 섹션 번호는 실제 데이터 유무와 관계없이 고정한다.
    # VNB Walk 데이터가 없더라도 1번 섹션을 표시한다.

    # ════════════════════════════════════════════════════════════
    # 1. VNB Walk
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 1) Key VNB Walk Movement"
        if is_english
        else "### 1) VNB Walk 핵심 변동"
    )

    if not vnb_walk_filtered.empty:
        step_impacts = compute_step_impacts(
            vnb_walk_filtered,
            step_order,
            ct_pq_anp,
            ct_cq_anp,
        )

        raw_deltas: dict[str, float] = {
            step: delta_value
            for step, (
                delta_value,
                margin_impact,
            ) in step_impacts.items()
        }

        raw_margin_impacts: dict[str, float] = {
            step: margin_impact
            for step, (
                delta_value,
                margin_impact,
            ) in step_impacts.items()
        }

        # ETU / TVOG / COMM은 Net 기준으로 결합한다.
        net_step_pairs = [
            (
                "PQ_ETU",
                "OTH_ETU",
                "NET_ETU",
            ),
            (
                "PQ_TVOG",
                "CQ_TVOG",
                "NET_TVOG",
            ),
            (
                "PQ_COMM",
                "OTH_COMM",
                "NET_COMM",
            ),
        ]

        for (
            first_step,
            second_step,
            net_step,
        ) in net_step_pairs:
            net_amount = (
                raw_deltas.pop(
                    first_step,
                    0.0,
                )
                + raw_deltas.pop(
                    second_step,
                    0.0,
                )
            )

            net_margin = (
                raw_margin_impacts.pop(
                    first_step,
                    0.0,
                )
                + raw_margin_impacts.pop(
                    second_step,
                    0.0,
                )
            )

            if net_amount or net_margin:
                raw_deltas[net_step] = net_amount
                raw_margin_impacts[net_step] = net_margin

        # PQ와 CQ는 시작 및 종료 절대값이므로 변동 Step 순위에서 제외한다.
        raw_deltas.pop(
            "PQ",
            None,
        )
        raw_deltas.pop(
            "CQ",
            None,
        )

        raw_margin_impacts.pop(
            "PQ",
            None,
        )
        raw_margin_impacts.pop(
            "CQ",
            None,
        )

        non_zero_margin_impacts = {
            step: impact
            for step, impact in raw_margin_impacts.items()
            if abs(impact) > 0
        }

        if non_zero_margin_impacts:
            top_step = max(
                non_zero_margin_impacts,
                key=lambda step: abs(
                    non_zero_margin_impacts[step]
                ),
            )

            top_margin_impact = float(
                raw_margin_impacts[
                    top_step
                ]
            )

            top_amount_impact = float(
                raw_deltas.get(
                    top_step,
                    0.0,
                )
            )

            if is_english:
                direction = (
                    "positive"
                    if top_margin_impact > 0
                    else (
                        "negative"
                        if top_margin_impact < 0
                        else "neutral"
                    )
                )

                lines.append(
                    f"- The largest Margin movement was "
                    f"**{top_step}**, with an impact of "
                    f"**{top_margin_impact:+.2f}%p** and a VNB impact of "
                    f"**{_fmt_amt(top_amount_impact, display_currency)}**."
                )

                lines.append(
                    f"- The Step had a **{direction}** impact on Margin."
                )

            else:
                direction = (
                    "Positive"
                    if top_margin_impact > 0
                    else (
                        "Negative"
                        if top_margin_impact < 0
                        else "Neutral"
                    )
                )

                lines.append(
                    f"- 가장 큰 Margin 변동 Step은 "
                    f"**{top_step}**으로, Margin 영향은 "
                    f"**{top_margin_impact:+.2f}%p**, VNB 영향은 "
                    f"**{_fmt_amt(top_amount_impact, display_currency)}**입니다."
                )

                lines.append(
                    f"- 해당 Step은 Margin에 **{direction} 영향**을 주었습니다."
                )

        else:
            lines.append(
                "- No material Margin movement was identified in the VNB Walk."
                if is_english
                else "- VNB Walk에서 유의미한 Margin 변동 Step이 확인되지 않았습니다."
            )

    else:
        lines.append(
            "- No VNB Walk data is available for the selected scope."
            if is_english
            else "- 선택한 범위의 VNB Walk 데이터가 없습니다."
        )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 2. Channel Mix
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 2) Channel Mix Changes"
        if is_english
        else "### 2) Channel Mix 변동"
    )

    channel_significant = pd.DataFrame()

    if (
        not ch_comp.empty
        and "Diff(%p)" in ch_comp.columns
    ):
        channel_significant = ch_comp[
            ch_comp["Diff(%p)"].abs()
            >= mix_threshold
        ].copy()

        channel_significant = channel_significant.reindex(
            channel_significant[
                "Diff(%p)"
            ].abs().sort_values(
                ascending=False
            ).index
        )

        if channel_significant.empty:
            if is_english:
                lines.append(
                    f"- All Channel Mix changes were within "
                    f"±{mix_threshold:.1f}%p, indicating a stable "
                    f"channel composition."
                )
            else:
                lines.append(
                    f"- 모든 Channel Mix 변동이 ±{mix_threshold:.1f}%p "
                    f"이내로 채널 구성이 안정적으로 유지되었습니다."
                )

        else:
            for _, row in channel_significant.head(3).iterrows():
                channel_name = row.get(
                    "CHANNEL",
                    "?",
                )

                mix_difference = float(
                    row.get(
                        "Diff(%p)",
                        0,
                    )
                )

                trend = _trend_word(
                    mix_difference,
                    language=language,
                )

                lines.append(
                    f"- **{channel_name}**: "
                    f"{_fmt_pct(row['Prev. Mix(%)'])} → "
                    f"{_fmt_pct(row['Curr. Mix(%)'])} "
                    f"({_fmt_pct(mix_difference, with_sign=True, suffix='%p')} "
                    f"{trend})"
                )

        # 선택 상품군 안에서 채널별 Margin과 Mix 변화 연결
        if (
            comp_table is not None
            and not comp_table.empty
        ):
            try:
                channel_margin_rows = comp_table.drop(
                    index=[
                        "TOTAL (Company)",
                        "Non-Model",
                    ],
                    errors="ignore",
                )

                has_total_row = (
                    "TOTAL (Company)"
                    in comp_table.index
                )

                has_margin_column = (
                    ("CURR", "VNB%")
                    in comp_table.columns
                )

                if (
                    not channel_margin_rows.empty
                    and has_total_row
                    and has_margin_column
                    and not channel_significant.empty
                ):
                    average_margin = float(
                        comp_table.loc[
                            "TOTAL (Company)",
                            ("CURR", "VNB%"),
                        ]
                    )

                    if is_english:
                        lines.append(
                            "\n**Relationship Between Channel Mix and Margin:**"
                        )
                    else:
                        lines.append(
                            "\n**Channel Mix와 Margin 간 관계:**"
                        )

                    for _, row in channel_significant.head(3).iterrows():
                        channel_name = row.get(
                            "CHANNEL",
                            "?",
                        )

                        mix_difference = float(
                            row.get(
                                "Diff(%p)",
                                0,
                            )
                        )

                        if channel_name not in channel_margin_rows.index:
                            continue

                        channel_margin = float(
                            channel_margin_rows.loc[
                                channel_name,
                                ("CURR", "VNB%"),
                            ]
                        )

                        if channel_margin > average_margin:
                            relative_level = (
                                "above"
                                if is_english
                                else "높은"
                            )

                        elif channel_margin < average_margin:
                            relative_level = (
                                "below"
                                if is_english
                                else "낮은"
                            )

                        else:
                            relative_level = (
                                "in line with"
                                if is_english
                                else "유사한"
                            )

                        above_average = (
                            channel_margin
                            > average_margin
                        )

                        contributes_to_improvement = (
                            (
                                mix_difference > 0
                                and above_average
                            )
                            or (
                                mix_difference < 0
                                and not above_average
                            )
                        )

                        if contributes_to_improvement:
                            effect = (
                                "contributed to Margin improvement"
                                if is_english
                                else "Margin 개선에 기여"
                            )
                        else:
                            effect = (
                                "was a source of Margin pressure"
                                if is_english
                                else "Margin 하락 요인"
                            )

                        mix_direction = _trend_word(
                            mix_difference,
                            language=language,
                        )

                        if is_english:
                            lines.append(
                                f"- **{channel_name}** Margin was "
                                f"{_fmt_pct(channel_margin)}, which was "
                                f"{relative_level} the selected Product Group "
                                f"average of {_fmt_pct(average_margin)}. "
                                f"The channel Mix showed an {mix_direction} and "
                                f"**{effect}**."
                            )
                        else:
                            lines.append(
                                f"- **{channel_name}** Margin은 "
                                f"{_fmt_pct(channel_margin)}로, 선택 상품군 평균 "
                                f"{_fmt_pct(average_margin)} 대비 {relative_level} 수준입니다. "
                                f"채널 비중이 {mix_direction}하여 **{effect}**했습니다."
                            )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                pass

    else:
        lines.append(
            "- No Channel Mix data is available."
            if is_english
            else "- Channel Mix 데이터가 없습니다."
        )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 3. Product Portfolio
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 3) Product Portfolio Changes"
        if is_english
        else "### 3) Product Portfolio 변동"
    )

    product_significant = pd.DataFrame()

    if (
        not pg_comp.empty
        and "Diff(%p)" in pg_comp.columns
    ):
        excluded_product_columns = {
            "Prev. Mix(%)",
            "Curr. Mix(%)",
            "Diff(%p)",
            "Prev. ANP",
            "Curr. ANP",
        }

        product_column = next(
            (
                column
                for column in pg_comp.columns
                if column not in excluded_product_columns
            ),
            "PRODUCT",
        )

        product_significant = pg_comp[
            pg_comp["Diff(%p)"].abs()
            >= mix_threshold
        ].copy()

        product_significant = product_significant.reindex(
            product_significant[
                "Diff(%p)"
            ].abs().sort_values(
                ascending=False
            ).index
        )

        if product_significant.empty:
            if is_english:
                lines.append(
                    f"- All Product Mix changes were within "
                    f"±{mix_threshold:.1f}%p, indicating a stable "
                    f"product portfolio."
                )
            else:
                lines.append(
                    f"- 모든 상품 Mix 변동이 ±{mix_threshold:.1f}%p "
                    f"이내로 상품 포트폴리오가 안정적으로 유지되었습니다."
                )

        else:
            for _, row in product_significant.head(3).iterrows():
                product_name = row.get(
                    product_column,
                    (
                        row.iloc[0]
                        if len(row) > 0
                        else "?"
                    ),
                )

                mix_difference = float(
                    row.get(
                        "Diff(%p)",
                        0,
                    )
                )

                trend = _trend_word(
                    mix_difference,
                    language=language,
                )

                lines.append(
                    f"- **{product_name}**: "
                    f"{_fmt_pct(row['Prev. Mix(%)'])} → "
                    f"{_fmt_pct(row['Curr. Mix(%)'])} "
                    f"({_fmt_pct(mix_difference, with_sign=True, suffix='%p')} "
                    f"{trend})"
                )

        # 선택 채널 안에서 상품군별 Margin과 Mix 변화 연결
        if (
            pg_table is not None
            and not pg_table.empty
        ):
            try:
                product_margin_rows = pg_table.drop(
                    index=[
                        "TOTAL (Company)",
                        "Non-Model",
                    ],
                    errors="ignore",
                )

                has_total_row = (
                    "TOTAL (Company)"
                    in pg_table.index
                )

                has_margin_column = (
                    ("CURR", "VNB%")
                    in pg_table.columns
                )

                if (
                    not product_margin_rows.empty
                    and has_total_row
                    and has_margin_column
                    and not product_significant.empty
                ):
                    average_product_margin = float(
                        pg_table.loc[
                            "TOTAL (Company)",
                            ("CURR", "VNB%"),
                        ]
                    )

                    if is_english:
                        lines.append(
                            "\n**Relationship Between Product Mix and Margin:**"
                        )
                    else:
                        lines.append(
                            "\n**Product Mix와 Margin 간 관계:**"
                        )

                    for _, row in product_significant.head(3).iterrows():
                        product_name = row.get(
                            product_column,
                            "?",
                        )

                        mix_difference = float(
                            row.get(
                                "Diff(%p)",
                                0,
                            )
                        )

                        if product_name not in product_margin_rows.index:
                            continue

                        product_margin = float(
                            product_margin_rows.loc[
                                product_name,
                                ("CURR", "VNB%"),
                            ]
                        )

                        if product_margin > average_product_margin:
                            relative_level = (
                                "above"
                                if is_english
                                else "높은"
                            )

                        elif product_margin < average_product_margin:
                            relative_level = (
                                "below"
                                if is_english
                                else "낮은"
                            )

                        else:
                            relative_level = (
                                "in line with"
                                if is_english
                                else "유사한"
                            )

                        above_average = (
                            product_margin
                            > average_product_margin
                        )

                        contributes_to_improvement = (
                            (
                                mix_difference > 0
                                and above_average
                            )
                            or (
                                mix_difference < 0
                                and not above_average
                            )
                        )

                        if contributes_to_improvement:
                            effect = (
                                "contributed to Margin improvement"
                                if is_english
                                else "Margin 개선에 기여"
                            )
                        else:
                            effect = (
                                "was a source of Margin pressure"
                                if is_english
                                else "Margin 하락 요인"
                            )

                        mix_direction = _trend_word(
                            mix_difference,
                            language=language,
                        )

                        if is_english:
                            lines.append(
                                f"- **{product_name}** Margin was "
                                f"{_fmt_pct(product_margin)}, which was "
                                f"{relative_level} the selected Channel average of "
                                f"{_fmt_pct(average_product_margin)}. "
                                f"The Product Mix showed an {mix_direction} and "
                                f"**{effect}**."
                            )
                        else:
                            lines.append(
                                f"- **{product_name}** Margin은 "
                                f"{_fmt_pct(product_margin)}로, 선택 채널 평균 "
                                f"{_fmt_pct(average_product_margin)} 대비 "
                                f"{relative_level} 수준입니다. "
                                f"상품 비중이 {mix_direction}하여 **{effect}**했습니다."
                            )

                # 현재 비중이 크면서 변동이 크지 않은 상품
                stable_large_products = pg_comp[
                    (
                        pg_comp["Curr. Mix(%)"] > 25
                    )
                    & (
                        pg_comp["Diff(%p)"].abs()
                        < mix_threshold
                    )
                ]

                if not stable_large_products.empty:
                    if is_english:
                        lines.append(
                            "\n**Large and Stable Product Mix:**"
                        )
                    else:
                        lines.append(
                            "\n**비중이 크고 안정적인 상품:**"
                        )

                    for _, row in stable_large_products.iterrows():
                        product_name = row.get(
                            product_column,
                            "?",
                        )

                        if is_english:
                            lines.append(
                                f"- **{product_name}** represented "
                                f"{_fmt_pct(row['Curr. Mix(%)'])} of current ANP. "
                                f"The Mix change was limited to "
                                f"{_fmt_pct(row['Diff(%p)'], with_sign=True, suffix='%p')}."
                            )
                        else:
                            lines.append(
                                f"- **{product_name}**의 당분기 비중은 "
                                f"{_fmt_pct(row['Curr. Mix(%)'])}이며, "
                                f"비중 변동은 "
                                f"{_fmt_pct(row['Diff(%p)'], with_sign=True, suffix='%p')}로 "
                                f"크지 않았습니다."
                            )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                pass

    else:
        lines.append(
            "- No Product Mix data is available."
            if is_english
            else "- Product Mix 데이터가 없습니다."
        )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 4. Contract Type Mix
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 4) Contract Type Mix Changes"
        if is_english
        else "### 4) Contract Type Mix 변동"
    )

    if (
        ct_comp is not None
        and not ct_comp.empty
        and "Diff(%p)" in ct_comp.columns
    ):
        excluded_contract_columns = {
            "Prev. Mix(%)",
            "Curr. Mix(%)",
            "Diff(%p)",
            "Prev. ANP",
            "Curr. ANP",
        }

        contract_column = next(
            (
                column
                for column in ct_comp.columns
                if column not in excluded_contract_columns
            ),
            "CONTRACT_TYPE",
        )

        contract_significant = ct_comp[
            ct_comp["Diff(%p)"].abs()
            >= mix_threshold
        ].copy()

        contract_significant = contract_significant.reindex(
            contract_significant[
                "Diff(%p)"
            ].abs().sort_values(
                ascending=False
            ).index
        )

        if contract_significant.empty:
            if is_english:
                lines.append(
                    f"- All Contract Type Mix changes were within "
                    f"±{mix_threshold:.1f}%p."
                )
            else:
                lines.append(
                    f"- 모든 Contract Type Mix 변동이 "
                    f"±{mix_threshold:.1f}%p 이내입니다."
                )

        else:
            for _, row in contract_significant.head(3).iterrows():
                contract_name = row.get(
                    contract_column,
                    (
                        row.iloc[0]
                        if len(row) > 0
                        else "?"
                    ),
                )

                mix_difference = float(
                    row.get(
                        "Diff(%p)",
                        0,
                    )
                )

                trend = _trend_word(
                    mix_difference,
                    language=language,
                )

                lines.append(
                    f"- **{contract_name}**: "
                    f"{_fmt_pct(row['Prev. Mix(%)'])} → "
                    f"{_fmt_pct(row['Curr. Mix(%)'])} "
                    f"({_fmt_pct(mix_difference, with_sign=True, suffix='%p')} "
                    f"{trend})"
                )

                contract_upper = str(
                    contract_name
                ).upper()

                if (
                    "RIDER" in contract_upper
                    or "AH" in contract_upper
                ):
                    if is_english:
                        rider_direction = (
                            "increased"
                            if mix_difference > 0
                            else (
                                "decreased"
                                if mix_difference < 0
                                else "was unchanged"
                            )
                        )

                        lines.append(
                            f"  - Rider-related business Mix "
                            f"**{rider_direction}**."
                        )
                    else:
                        rider_direction = (
                            "증가"
                            if mix_difference > 0
                            else (
                                "감소"
                                if mix_difference < 0
                                else "보합"
                            )
                        )

                        lines.append(
                            f"  - Rider 관련 계약 비중이 "
                            f"**{rider_direction}**했습니다."
                        )

    else:
        lines.append(
            "- No Contract Type Mix data is available."
            if is_english
            else "- Contract Type Mix 데이터가 없습니다."
        )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 5. Combined Assessment
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 5) Combined Assessment"
        if is_english
        else "### 5) 종합 진단"
    )

    key_findings: list[str] = []

    if not channel_significant.empty:
        top_channel_row = channel_significant.iloc[0]
        top_channel_name = top_channel_row.get(
            "CHANNEL",
            "?",
        )
        top_channel_change = float(
            top_channel_row.get(
                "Diff(%p)",
                0,
            )
        )

        if is_english:
            key_findings.append(
                f"- The largest Channel Mix movement was observed in "
                f"**{top_channel_name}** at "
                f"{_fmt_pct(top_channel_change, with_sign=True, suffix='%p')}."
            )
        else:
            key_findings.append(
                f"- 가장 큰 Channel Mix 변동은 "
                f"**{top_channel_name}**의 "
                f"{_fmt_pct(top_channel_change, with_sign=True, suffix='%p')}입니다."
            )

    if not product_significant.empty:
        excluded_product_columns = {
            "Prev. Mix(%)",
            "Curr. Mix(%)",
            "Diff(%p)",
            "Prev. ANP",
            "Curr. ANP",
        }

        product_column = next(
            (
                column
                for column in pg_comp.columns
                if column not in excluded_product_columns
            ),
            "PRODUCT",
        )

        top_product_row = product_significant.iloc[0]

        top_product_name = top_product_row.get(
            product_column,
            "?",
        )

        top_product_change = float(
            top_product_row.get(
                "Diff(%p)",
                0,
            )
        )

        if is_english:
            key_findings.append(
                f"- The largest Product Mix movement was observed in "
                f"**{top_product_name}** at "
                f"{_fmt_pct(top_product_change, with_sign=True, suffix='%p')}."
            )
        else:
            key_findings.append(
                f"- 가장 큰 Product Mix 변동은 "
                f"**{top_product_name}**의 "
                f"{_fmt_pct(top_product_change, with_sign=True, suffix='%p')}입니다."
            )

    if key_findings:
        lines.extend(
            key_findings
        )

        if is_english:
            lines.append(
                "- Review whether the direction of these Mix changes is "
                "consistent with the relative Margin level of the affected "
                "channels and products."
            )
        else:
            lines.append(
                "- 주요 채널 및 상품의 Mix 변화 방향이 해당 항목의 "
                "상대적 Margin 수준과 일치하는지 함께 점검할 필요가 있습니다."
            )

    else:
        lines.append(
            "- No material Sales Mix movement was identified for the selected scope."
            if is_english
            else "- 선택한 범위에서 유의미한 Sales Mix 변동이 확인되지 않았습니다."
        )

    lines.append("")

    return "\n".join(lines)