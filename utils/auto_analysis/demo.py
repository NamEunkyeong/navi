"""
utils/auto_analysis/demo.py
───────────────────────────
Demo 탭 자동 분석 초안 생성.

분석 범위
---------
- Product Mix
- Average Ticket Size
- Premium Term
- Age Group
- Deferment Period
- Combined Insights

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


def generate_demo_draft(
    target_pg: str,
    target_ch: str,
    prod_comp: pd.DataFrame,
    ts_comp: pd.DataFrame,
    term_comp: pd.DataFrame,
    age_comp: pd.DataFrame,
    display_currency: str,
    mix_threshold: float = 1.0,
    avg_defer_prev: float | None = None,
    avg_defer_curr: float | None = None,
    language: str = "Korean",
) -> str:
    """
    Demo 탭 자동 분석 초안을 생성한다.

    Parameters
    ----------
    target_pg:
        선택한 Product Group.

    target_ch:
        선택한 Channel.

    prod_comp:
        상품별 전분기/당분기 Mix 비교 DataFrame.

    ts_comp:
        상품별 전분기/당분기 Ticket Size 비교 DataFrame.

    term_comp:
        납입기간별 전분기/당분기 Mix 비교 DataFrame.

    age_comp:
        연령대별 전분기/당분기 Mix 비교 DataFrame.

    display_currency:
        KRW 또는 USD.

    mix_threshold:
        유의미한 Mix 변동으로 판단할 기준 Percentage Point.

    avg_defer_prev:
        전분기 평균 거치기간.

    avg_defer_curr:
        당분기 평균 거치기간.

    language:
        Korean 또는 English.
    """
    is_english = _is_english(language)

    lines: list[str] = []

    scope = (
        f"{target_pg} × {target_ch}"
    )

    lines.append(
        (
            f"## 👥 Demographics & Product Detail Analysis – {scope}\n"
            if is_english
            else f"## 👥 인구통계 및 상품 상세 분석 – {scope}\n"
        )
    )

    has_any_data = False

    # ════════════════════════════════════════════════════════════
    # 1. Product Mix
    # ════════════════════════════════════════════════════════════
    if (
        not prod_comp.empty
        and "Diff(%p)" in prod_comp.columns
    ):
        has_any_data = True

        lines.append(
            "### 1) Product Mix Changes"
            if is_english
            else "### 1) 상품 구성 변동"
        )

        significant_products = prod_comp[
            prod_comp["Diff(%p)"].abs()
            >= mix_threshold
        ].copy()

        significant_products = significant_products.reindex(
            significant_products[
                "Diff(%p)"
            ].abs().sort_values(
                ascending=False
            ).index
        )

        if significant_products.empty:
            if is_english:
                lines.append(
                    f"- All product-level Mix changes were within "
                    f"±{mix_threshold:.1f}%p, indicating a stable "
                    f"product portfolio."
                )
            else:
                lines.append(
                    f"- 상품별 Mix 변동이 모두 ±{mix_threshold:.1f}%p "
                    f"이내로 상품 포트폴리오가 안정적으로 유지되었습니다."
                )

        else:
            excluded_columns = {
                "Prev. Mix(%)",
                "Curr. Mix(%)",
                "Diff(%p)",
            }

            product_column = next(
                (
                    column
                    for column in prod_comp.columns
                    if column not in excluded_columns
                ),
                "PRODUCT",
            )

            for _, row in significant_products.head(3).iterrows():
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

                if is_english:
                    lines.append(
                        f"- **{product_name}**: "
                        f"{_fmt_pct(row['Prev. Mix(%)'])} → "
                        f"{_fmt_pct(row['Curr. Mix(%)'])} "
                        f"({_fmt_pct(mix_difference, with_sign=True, suffix='%p')} "
                        f"{trend})"
                    )
                else:
                    lines.append(
                        f"- **{product_name}**: "
                        f"{_fmt_pct(row['Prev. Mix(%)'])} → "
                        f"{_fmt_pct(row['Curr. Mix(%)'])} "
                        f"({_fmt_pct(mix_difference, with_sign=True, suffix='%p')} "
                        f"{trend})"
                    )

        lines.append("")

    # ════════════════════════════════════════════════════════════
    # 2. Average Ticket Size
    # ════════════════════════════════════════════════════════════
    if (
        not ts_comp.empty
        and "Growth(%)" in ts_comp.columns
    ):
        has_any_data = True

        lines.append(
            "### 2) Average Ticket Size Changes"
            if is_english
            else "### 2) 평균 Ticket Size 변화"
        )

        meaningful_ticket_size = ts_comp[
            ts_comp["Prev. TS"] != 0
        ].copy()

        if not meaningful_ticket_size.empty:
            sorted_ticket_size = meaningful_ticket_size.reindex(
                meaningful_ticket_size[
                    "Growth(%)"
                ].abs().sort_values(
                    ascending=False
                ).index
            )

            ticket_product_column = next(
                (
                    column
                    for column in ts_comp.columns
                    if column not in {
                        "Prev. TS",
                        "Curr. TS",
                        "Growth(%)",
                    }
                ),
                "PRODUCT",
            )

            overall_ticket_growth = float(
                meaningful_ticket_size[
                    "Growth(%)"
                ].mean()
            )

            if overall_ticket_growth > 2:
                if is_english:
                    lines.append(
                        f"- 📈 Average Ticket Size increased by "
                        f"**{overall_ticket_growth:+.1f}%** on average. "
                        f"The increase may reduce per-policy expense pressure "
                        f"and have a **positive impact on VNB**."
                    )
                else:
                    lines.append(
                        f"- 📈 평균 Ticket Size가 평균 "
                        f"**{overall_ticket_growth:+.1f}% 증가**했습니다. "
                        f"건당 비용 부담 감소를 통해 **VNB에 Positive 영향**을 "
                        f"줄 수 있습니다."
                    )

            elif overall_ticket_growth < -2:
                if is_english:
                    lines.append(
                        f"- 📉 Average Ticket Size decreased by "
                        f"**{overall_ticket_growth:+.1f}%** on average. "
                        f"A greater proportion of smaller policies may increase "
                        f"per-policy expense pressure and have a "
                        f"**negative impact on VNB**."
                    )
                else:
                    lines.append(
                        f"- 📉 평균 Ticket Size가 평균 "
                        f"**{overall_ticket_growth:+.1f}% 감소**했습니다. "
                        f"소액 계약 증가에 따른 건당 비용 부담 상승으로 "
                        f"**VNB에 Negative 영향**을 줄 수 있습니다."
                    )

            else:
                if is_english:
                    lines.append(
                        f"- Average Ticket Size was broadly stable, with an "
                        f"average change of **{overall_ticket_growth:+.1f}%**."
                    )
                else:
                    lines.append(
                        f"- 평균 Ticket Size 변동은 "
                        f"**{overall_ticket_growth:+.1f}%**로 보합 수준입니다."
                    )

            for _, row in sorted_ticket_size.head(3).iterrows():
                product_name = row.get(
                    ticket_product_column,
                    (
                        row.iloc[0]
                        if len(row) > 0
                        else "?"
                    ),
                )

                growth = float(
                    row.get(
                        "Growth(%)",
                        0,
                    )
                )

                if growth > 2:
                    effect = (
                        "✅ Lower per-policy expense pressure → Positive"
                        if is_english
                        else "✅ 건당 비용 부담 감소 → Positive"
                    )

                elif growth < -2:
                    effect = (
                        "⚠️ Higher per-policy expense pressure → Negative"
                        if is_english
                        else "⚠️ 건당 비용 부담 증가 → Negative"
                    )

                else:
                    effect = (
                        "→ Limited impact"
                        if is_english
                        else "→ 영향 미미"
                    )

                lines.append(
                    f"- **{product_name}**: "
                    f"{_fmt_amt(row['Prev. TS'], display_currency)} → "
                    f"{_fmt_amt(row['Curr. TS'], display_currency)} "
                    f"({_fmt_pct(growth, with_sign=True)}) {effect}"
                )

        else:
            lines.append(
                "- Comparison is unavailable because previous-quarter data is missing."
                if is_english
                else "- 전분기 데이터가 없어 Ticket Size 비교가 어렵습니다."
            )

        lines.append("")

    # ════════════════════════════════════════════════════════════
    # 3. Premium Term
    # ════════════════════════════════════════════════════════════
    if not term_comp.empty:
        has_any_data = True

        lines.append(
            "### 3) Premium Term Distribution"
            if is_english
            else "### 3) 납입기간(Premium Term) 분포"
        )

        term_data = term_comp.copy()

        required_term_columns = {
            "Prev. Mix(%)",
            "Curr. Mix(%)",
        }

        if required_term_columns.issubset(
            term_data.columns
        ):
            term_data["Diff(%p)"] = (
                term_data["Curr. Mix(%)"]
                - term_data["Prev. Mix(%)"]
            )

            significant_terms = term_data[
                term_data["Diff(%p)"].abs()
                >= mix_threshold
            ].copy()

            significant_terms = significant_terms.reindex(
                significant_terms[
                    "Diff(%p)"
                ].abs().sort_values(
                    ascending=False
                ).index
            )

            if significant_terms.empty:
                if is_english:
                    lines.append(
                        f"- All premium-term Mix changes were within "
                        f"±{mix_threshold:.1f}%p."
                    )
                else:
                    lines.append(
                        f"- 납입기간별 Mix 변동이 모두 "
                        f"±{mix_threshold:.1f}%p 이내입니다."
                    )

            else:
                for _, row in significant_terms.head(3).iterrows():
                    premium_term = row.get(
                        "Term",
                        "?",
                    )

                    term_difference = float(
                        row.get(
                            "Diff(%p)",
                            0,
                        )
                    )

                    trend = _trend_word(
                        term_difference,
                        language=language,
                    )

                    term_label = (
                        f"{premium_term} years"
                        if is_english
                        else f"{premium_term}년"
                    )

                    lines.append(
                        f"- **{term_label}**: "
                        f"{_fmt_pct(row['Prev. Mix(%)'])} → "
                        f"{_fmt_pct(row['Curr. Mix(%)'])} "
                        f"({_fmt_pct(term_difference, with_sign=True, suffix='%p')} "
                        f"{trend})"
                    )

            # 장기납 비중
            try:
                term_data["TermNum"] = pd.to_numeric(
                    term_data["Term"],
                    errors="coerce",
                )

                previous_long_term_mix = float(
                    term_data.loc[
                        term_data["TermNum"] >= 20,
                        "Prev. Mix(%)",
                    ].sum()
                )

                current_long_term_mix = float(
                    term_data.loc[
                        term_data["TermNum"] >= 20,
                        "Curr. Mix(%)",
                    ].sum()
                )

                long_term_difference = (
                    current_long_term_mix
                    - previous_long_term_mix
                )

                if (
                    previous_long_term_mix > 0
                    or current_long_term_mix > 0
                ):
                    if is_english:
                        lines.append(
                            f"- Mix of long premium terms of 20 years or more: "
                            f"{_fmt_pct(previous_long_term_mix)} → "
                            f"{_fmt_pct(current_long_term_mix)} "
                            f"({_fmt_pct(long_term_difference, with_sign=True, suffix='%p')})"
                        )
                    else:
                        lines.append(
                            f"- 장기납(20년 이상) 비중: "
                            f"{_fmt_pct(previous_long_term_mix)} → "
                            f"{_fmt_pct(current_long_term_mix)} "
                            f"({_fmt_pct(long_term_difference, with_sign=True, suffix='%p')})"
                        )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                pass

        lines.append("")

    # ════════════════════════════════════════════════════════════
    # 4. Age Group
    # ════════════════════════════════════════════════════════════
    if not age_comp.empty:
        has_any_data = True

        lines.append(
            "### 4) Age Group Distribution"
            if is_english
            else "### 4) 연령대(Age Group) 분포"
        )

        age_data = age_comp.copy()

        required_age_columns = {
            "Prev. Mix(%)",
            "Curr. Mix(%)",
        }

        if required_age_columns.issubset(
            age_data.columns
        ):
            if "Diff(%p)" not in age_data.columns:
                age_data["Diff(%p)"] = (
                    age_data["Curr. Mix(%)"]
                    - age_data["Prev. Mix(%)"]
                )

            significant_ages = age_data[
                age_data["Diff(%p)"].abs()
                >= mix_threshold
            ].copy()

            significant_ages = significant_ages.reindex(
                significant_ages[
                    "Diff(%p)"
                ].abs().sort_values(
                    ascending=False
                ).index
            )

            higher_age_groups = [
                "50s",
                "60s",
                "Over 70",
            ]

            higher_age_rows = age_data[
                age_data["Age Group"].isin(
                    higher_age_groups
                )
            ]

            if not higher_age_rows.empty:
                previous_higher_age_mix = float(
                    higher_age_rows[
                        "Prev. Mix(%)"
                    ].sum()
                )

                current_higher_age_mix = float(
                    higher_age_rows[
                        "Curr. Mix(%)"
                    ].sum()
                )

                higher_age_difference = (
                    current_higher_age_mix
                    - previous_higher_age_mix
                )

                if abs(higher_age_difference) >= mix_threshold:
                    if higher_age_difference > 0:
                        if is_english:
                            lines.append(
                                f"- 📉 Mix of customers aged 50 and over increased "
                                f"from {_fmt_pct(previous_higher_age_mix)} to "
                                f"**{_fmt_pct(current_higher_age_mix)}** "
                                f"({_fmt_pct(higher_age_difference, with_sign=True, suffix='%p')}). "
                                f"This may have a **negative impact on VNB**."
                            )
                        else:
                            lines.append(
                                f"- 📉 50세 이상 고연령 비중이 "
                                f"{_fmt_pct(previous_higher_age_mix)}에서 "
                                f"**{_fmt_pct(current_higher_age_mix)}**로 증가했습니다 "
                                f"({_fmt_pct(higher_age_difference, with_sign=True, suffix='%p')}). "
                                f"이는 **VNB에 Negative 영향**을 줄 수 있습니다."
                            )

                    else:
                        if is_english:
                            lines.append(
                                f"- 📈 Mix of customers aged 50 and over decreased "
                                f"from {_fmt_pct(previous_higher_age_mix)} to "
                                f"**{_fmt_pct(current_higher_age_mix)}** "
                                f"({_fmt_pct(higher_age_difference, with_sign=True, suffix='%p')}). "
                                f"This may have a **positive impact on VNB**."
                            )
                        else:
                            lines.append(
                                f"- 📈 50세 이상 고연령 비중이 "
                                f"{_fmt_pct(previous_higher_age_mix)}에서 "
                                f"**{_fmt_pct(current_higher_age_mix)}**로 감소했습니다 "
                                f"({_fmt_pct(higher_age_difference, with_sign=True, suffix='%p')}). "
                                f"이는 **VNB에 Positive 영향**을 줄 수 있습니다."
                            )

                else:
                    if is_english:
                        lines.append(
                            f"- Mix of customers aged 50 and over was "
                            f"{_fmt_pct(current_higher_age_mix)}, with limited "
                            f"change from the previous quarter."
                        )
                    else:
                        lines.append(
                            f"- 50세 이상 고연령 비중은 "
                            f"{_fmt_pct(current_higher_age_mix)}로 "
                            f"전분기 대비 변동이 크지 않습니다."
                        )

            if significant_ages.empty:
                if is_english:
                    lines.append(
                        f"- All age-group Mix changes were within "
                        f"±{mix_threshold:.1f}%p."
                    )
                else:
                    lines.append(
                        f"- 연령대별 Mix 변동이 모두 "
                        f"±{mix_threshold:.1f}%p 이내입니다."
                    )

            else:
                for _, row in significant_ages.head(3).iterrows():
                    age_group = row.get(
                        "Age Group",
                        "?",
                    )

                    difference = float(
                        row.get(
                            "Diff(%p)",
                            0,
                        )
                    )

                    is_higher_age = (
                        str(age_group)
                        in higher_age_groups
                    )

                    if is_higher_age:
                        if difference > 0:
                            effect = (
                                "⚠️ Potential negative VNB impact"
                                if is_english
                                else "⚠️ VNB Negative 요인"
                            )
                        else:
                            effect = (
                                "✅ Potential positive VNB impact"
                                if is_english
                                else "✅ VNB Positive 요인"
                            )

                    else:
                        if difference > 0:
                            effect = (
                                "✅ Potential positive VNB impact"
                                if is_english
                                else "✅ VNB Positive 요인"
                            )
                        else:
                            effect = (
                                "⚠️ Further VNB impact review required"
                                if is_english
                                else "⚠️ VNB 영향 추가 점검 필요"
                            )

                    lines.append(
                        f"- **{age_group}**: "
                        f"{_fmt_pct(row['Prev. Mix(%)'])} → "
                        f"{_fmt_pct(row['Curr. Mix(%)'])} "
                        f"({_fmt_pct(difference, with_sign=True, suffix='%p')}) "
                        f"{effect}"
                    )

        lines.append("")

    # ════════════════════════════════════════════════════════════
    # 5. Average Deferment Period
    # ════════════════════════════════════════════════════════════
    if (
        avg_defer_curr is not None
        or avg_defer_prev is not None
    ):
        has_any_data = True

        lines.append(
            "### 5) Average Deferment Period for Contracts with DEFER_Y > 0"
            if is_english
            else "### 5) 평균 거치기간 (DEFER_Y > 0 계약)"
        )

        previous_deferment_text = (
            (
                f"{avg_defer_prev:.2f} years"
                if is_english
                else f"{avg_defer_prev:.2f}년"
            )
            if avg_defer_prev is not None
            else "N/A"
        )

        current_deferment_text = (
            (
                f"{avg_defer_curr:.2f} years"
                if is_english
                else f"{avg_defer_curr:.2f}년"
            )
            if avg_defer_curr is not None
            else "N/A"
        )

        lines.append(
            (
                f"- Previous-quarter average: **{previous_deferment_text}**"
                if is_english
                else f"- 전분기 평균: **{previous_deferment_text}**"
            )
        )

        lines.append(
            (
                f"- Current-quarter average: **{current_deferment_text}**"
                if is_english
                else f"- 당분기 평균: **{current_deferment_text}**"
            )
        )

        if (
            avg_defer_curr is not None
            and avg_defer_prev is not None
        ):
            deferment_difference = (
                avg_defer_curr
                - avg_defer_prev
            )

            trend = _trend_word(
                deferment_difference,
                language=language,
            )

            if deferment_difference > 0:
                interpretation = (
                    "Preference for longer deferment periods increased."
                    if is_english
                    else "장기 거치 선호도가 상승했습니다."
                )

            elif deferment_difference < 0:
                interpretation = (
                    "The Mix shifted toward shorter deferment periods "
                    "or immediate annuities."
                    if is_english
                    else "단기 거치 또는 즉시연금 방향으로 Mix가 이동했습니다."
                )

            else:
                interpretation = (
                    "There was no meaningful change in the average deferment period."
                    if is_english
                    else "평균 거치기간에 유의미한 변동이 없습니다."
                )

            unit_text = (
                "years"
                if is_english
                else "년"
            )

            lines.append(
                (
                    f"- Change: {deferment_difference:+.2f} {unit_text} "
                    f"({trend}). {interpretation}"
                )
            )

        lines.append("")

    # ════════════════════════════════════════════════════════════
    # 6. Combined Insights
    # ════════════════════════════════════════════════════════════
    if has_any_data:
        lines.append(
            "### 6) Combined Insights"
            if is_english
            else "### 6) 종합 인사이트"
        )

        insights: list[str] = []

        # Product Mix + Ticket Size
        if (
            not prod_comp.empty
            and not ts_comp.empty
            and "Diff(%p)" in prod_comp.columns
        ):
            product_mix_column = next(
                (
                    column
                    for column in prod_comp.columns
                    if column not in {
                        "Prev. Mix(%)",
                        "Curr. Mix(%)",
                        "Diff(%p)",
                    }
                ),
                None,
            )

            ticket_product_column = next(
                (
                    column
                    for column in ts_comp.columns
                    if column not in {
                        "Prev. TS",
                        "Curr. TS",
                        "Growth(%)",
                    }
                ),
                None,
            )

            top_product = prod_comp.reindex(
                prod_comp[
                    "Diff(%p)"
                ].abs().sort_values(
                    ascending=False
                ).index
            ).head(1)

            if (
                not top_product.empty
                and product_mix_column
                and ticket_product_column
            ):
                product_name = top_product.iloc[0].get(
                    product_mix_column,
                    None,
                )

                if (
                    product_name is not None
                    and product_name
                    in ts_comp[ticket_product_column].values
                ):
                    ticket_row = ts_comp[
                        ts_comp[ticket_product_column]
                        == product_name
                    ].iloc[0]

                    mix_direction = _trend_word(
                        float(
                            top_product.iloc[0][
                                "Diff(%p)"
                            ]
                        ),
                        language=language,
                    )

                    ticket_growth = float(
                        ticket_row.get(
                            "Growth(%)",
                            0,
                        )
                    )

                    ticket_direction = _trend_word(
                        ticket_growth,
                        language=language,
                    )

                    if is_english:
                        insights.append(
                            f"- The Mix of **{product_name}** showed an "
                            f"{mix_direction}, while its average Ticket Size "
                            f"showed a {ticket_direction} "
                            f"({_fmt_pct(ticket_growth, with_sign=True)}). "
                            f"Sales Mix and policy size should be reviewed together."
                        )
                    else:
                        insights.append(
                            f"- **{product_name}**의 비중이 {mix_direction}하는 가운데 "
                            f"평균 Ticket Size는 {ticket_direction}했습니다 "
                            f"({_fmt_pct(ticket_growth, with_sign=True)}). "
                            f"판매 Mix와 건당 규모를 함께 점검할 필요가 있습니다."
                        )

        # Age Group + Premium Term
        if (
            not age_comp.empty
            and not term_comp.empty
        ):
            try:
                age_analysis = age_comp.copy()
                term_analysis = term_comp.copy()

                if "Diff(%p)" not in age_analysis.columns:
                    age_analysis["Diff(%p)"] = (
                        age_analysis["Curr. Mix(%)"]
                        - age_analysis["Prev. Mix(%)"]
                    )

                if "Diff(%p)" not in term_analysis.columns:
                    term_analysis["Diff(%p)"] = (
                        term_analysis["Curr. Mix(%)"]
                        - term_analysis["Prev. Mix(%)"]
                    )

                top_age = age_analysis.reindex(
                    age_analysis[
                        "Diff(%p)"
                    ].abs().sort_values(
                        ascending=False
                    ).index
                ).head(1)

                top_term = term_analysis.reindex(
                    term_analysis[
                        "Diff(%p)"
                    ].abs().sort_values(
                        ascending=False
                    ).index
                ).head(1)

                if (
                    not top_age.empty
                    and not top_term.empty
                ):
                    age_group = top_age.iloc[0].get(
                        "Age Group",
                        "?",
                    )

                    term = top_term.iloc[0].get(
                        "Term",
                        "?",
                    )

                    age_change = float(
                        top_age.iloc[0][
                            "Diff(%p)"
                        ]
                    )

                    term_change = float(
                        top_term.iloc[0][
                            "Diff(%p)"
                        ]
                    )

                    if is_english:
                        insights.append(
                            f"- The Mix of the **{age_group}** age group changed by "
                            f"{_fmt_pct(age_change, with_sign=True, suffix='%p')}, "
                            f"while the Mix of the **{term}-year** premium term "
                            f"changed by "
                            f"{_fmt_pct(term_change, with_sign=True, suffix='%p')}. "
                            f"The change in customer purchasing behavior should be reviewed."
                        )
                    else:
                        insights.append(
                            f"- 가입 연령은 **{age_group}** 비중이 "
                            f"{_fmt_pct(age_change, with_sign=True, suffix='%p')} 변동했고, "
                            f"납입기간은 **{term}년** 비중이 "
                            f"{_fmt_pct(term_change, with_sign=True, suffix='%p')} 변동했습니다. "
                            f"타깃 고객군의 가입 행태 변화를 점검할 필요가 있습니다."
                        )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                pass

        if insights:
            lines.extend(insights)

        else:
            lines.append(
                "- Additional segment-level analysis is recommended when more data becomes available."
                if is_english
                else "- 추가 데이터 확보 후 세그먼트 간 결합 분석을 권장합니다."
            )

    else:
        lines.append(
            "⚠️ Insufficient data is available for the analysis. Review the selected filters."
            if is_english
            else "⚠️ 분석에 필요한 데이터가 부족합니다. 선택한 필터 조건을 확인해주세요."
        )

    lines.append("")

    return "\n".join(lines)