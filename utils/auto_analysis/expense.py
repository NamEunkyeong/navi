"""
utils/auto_analysis/expense.py
──────────────────────────────
Expense 탭 자동 분석 초안 생성.

Korean / English Markdown 분석 보고서를 생성한다.
"""

from __future__ import annotations

import pandas as pd

from ._common import _is_english


def generate_expense_draft(
    target_scope: str,
    df_exp: pd.DataFrame,
    display_currency: str,
    language: str = "Korean",
) -> str:
    """
    Expense 탭 분석 초안을 생성한다.

    Parameters
    ----------
    target_scope:
        선택한 채널 또는 Company Total.

    df_exp:
        Expense 비교 DataFrame.

    display_currency:
        KRW 또는 USD.

    language:
        Korean 또는 English.

    Expected columns
    ----------------
    - Actual
    - Model
    - Actual / Model
    - Actual - Model
    - AFT_TAX
    """
    is_english = _is_english(language)

    currency_symbol = (
        "$"
        if display_currency == "USD"
        else "₩"
    )

    def format_amount(
        value: float,
    ) -> str:
        """Expense 금액을 Millions 단위로 표시한다."""
        if pd.isna(value):
            return "-"

        return (
            f"{currency_symbol}"
            f"{float(value):,.1f}M"
        )

    def format_ratio(
        value: float,
    ) -> str:
        """Actual / Model 비율을 안전하게 표시한다."""
        if pd.isna(value):
            return "-"

        return f"{float(value):.4f}"

    lines: list[str] = []

    if is_english:
        lines.append(
            f"## 🧾 Expense Variance Analysis – {target_scope}\n"
        )
    else:
        lines.append(
            f"## 🧾 Expense 편차 분석 – {target_scope}\n"
        )

    if (
        df_exp.empty
        or "TOTAL" not in df_exp.index
    ):
        lines.append(
            "⚠️ No expense data is available."
            if is_english
            else "⚠️ Expense 데이터가 없습니다."
        )

        return "\n".join(lines)

    total_row = df_exp.loc["TOTAL"]

    total_ratio = float(
        total_row.get(
            "Actual / Model",
            0,
        )
        or 0
    )

    total_actual = float(
        total_row.get(
            "Actual",
            0,
        )
        or 0
    )

    total_model = float(
        total_row.get(
            "Model",
            0,
        )
        or 0
    )

    total_difference = float(
        total_row.get(
            "Actual - Model",
            0,
        )
        or 0
    )

    total_after_tax = float(
        total_row.get(
            "AFT_TAX",
            0,
        )
        or 0
    )

    # ════════════════════════════════════════════════════════════
    # 1. Total Expense Summary
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 1) Total Expense Summary (Unit: Millions)"
        if is_english
        else "### 1) 총 비용 요약 (단위: Millions)"
    )

    lines.append(
        f"- Actual: **{format_amount(total_actual)}** / "
        f"Model: **{format_amount(total_model)}** "
        f"= {format_ratio(total_ratio)} "
        f"({(total_ratio - 1) * 100:+.2f}%)"
    )

    if is_english:
        lines.append(
            f"- Actual minus Model: "
            f"**{format_amount(total_difference)}**"
        )

        lines.append(
            f"- After-tax impact: "
            f"**{format_amount(total_after_tax)}**"
        )
    else:
        lines.append(
            f"- Actual - Model: "
            f"**{format_amount(total_difference)}**"
        )

        lines.append(
            f"- 세후 영향(AFT_TAX): "
            f"**{format_amount(total_after_tax)}**"
        )

    if total_difference > 0:
        total_interpretation = (
            "Actual expenses exceeded the model assumption."
            if is_english
            else "Actual 비용이 Model 가정을 초과했습니다."
        )

    elif total_difference < 0:
        total_interpretation = (
            "Actual expenses were below the model assumption."
            if is_english
            else "Actual 비용이 Model 가정보다 낮았습니다."
        )

    else:
        total_interpretation = (
            "Actual expenses were in line with the model assumption."
            if is_english
            else "Actual 비용과 Model 가정이 동일한 수준입니다."
        )

    lines.append(
        f"- {total_interpretation}"
    )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 2. Actual vs Model by Category
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 2) Actual vs Model by Category"
        if is_english
        else "### 2) 항목별 Actual vs Model"
    )

    detail_rows = [
        "ANP",
        "SC",
        "PNI",
        "COMM",
    ]

    available_detail_count = 0

    for category in detail_rows:
        if category not in df_exp.index:
            continue

        available_detail_count += 1

        row = df_exp.loc[category]

        actual_value = float(
            row.get(
                "Actual",
                0,
            )
            or 0
        )

        model_value = float(
            row.get(
                "Model",
                0,
            )
            or 0
        )

        actual_model_ratio = float(
            row.get(
                "Actual / Model",
                0,
            )
            or 0
        )

        difference = float(
            row.get(
                "Actual - Model",
                0,
            )
            or 0
        )

        if is_english:
            direction = (
                "above Model"
                if difference > 0
                else (
                    "below Model"
                    if difference < 0
                    else "in line with Model"
                )
            )

            lines.append(
                f"- **{category}**: "
                f"Actual {format_amount(actual_value)} / "
                f"Model {format_amount(model_value)} "
                f"(×{actual_model_ratio:.4f}, "
                f"{format_amount(difference)} {direction})"
            )

        else:
            direction = (
                "Model 초과"
                if difference > 0
                else (
                    "Model 미달"
                    if difference < 0
                    else "Model과 동일"
                )
            )

            lines.append(
                f"- **{category}**: "
                f"Actual {format_amount(actual_value)} / "
                f"Model {format_amount(model_value)} "
                f"(×{actual_model_ratio:.4f}, "
                f"{format_amount(difference)} {direction})"
            )

    if available_detail_count == 0:
        lines.append(
            "- No category-level expense data is available."
            if is_english
            else "- 항목별 Expense 데이터가 없습니다."
        )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 3. Key Variance
    # ════════════════════════════════════════════════════════════
    detail_dataframe = df_exp.loc[
        [
            category
            for category in detail_rows
            if category in df_exp.index
        ]
    ].copy()

    if (
        not detail_dataframe.empty
        and "Actual - Model" in detail_dataframe.columns
    ):
        largest_variance_category = (
            detail_dataframe[
                "Actual - Model"
            ]
            .abs()
            .idxmax()
        )

        largest_variance_row = (
            detail_dataframe.loc[
                largest_variance_category
            ]
        )

        largest_variance = float(
            largest_variance_row.get(
                "Actual - Model",
                0,
            )
            or 0
        )

        lines.append(
            "### 3) Key Expense Variance"
            if is_english
            else "### 3) 주요 Expense 편차"
        )

        if is_english:
            lines.append(
                f"- **{largest_variance_category}** had the largest "
                f"absolute variance at "
                f"**{format_amount(largest_variance)}**."
            )

            lines.append(
                "- Review the underlying unit cost, volume and "
                "timing assumptions for the category."
            )

        else:
            lines.append(
                f"- 절대값 기준 가장 큰 편차는 "
                f"**{largest_variance_category}**의 "
                f"**{format_amount(largest_variance)}**입니다."
            )

            lines.append(
                "- 해당 항목의 단위 비용, 물량 및 비용 인식 시점 "
                "가정을 추가 점검할 필요가 있습니다."
            )

        lines.append("")

    return "\n".join(lines)