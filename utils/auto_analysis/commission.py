"""
utils/auto_analysis/commission.py
─────────────────────────────────
Commission 탭 자동 분석 초안 생성.

Korean / English Markdown 분석 보고서를 생성한다.
"""

from __future__ import annotations

import pandas as pd

from ._common import _is_english


def generate_commission_draft(
    target_ch: str,
    df_comm: pd.DataFrame,
    display_currency: str,
    language: str = "Korean",
) -> str:
    """
    Commission 탭 분석 초안을 생성한다.

    Parameters
    ----------
    target_ch:
        선택 채널 또는 선택 범위.

    df_comm:
        Commission 비교 DataFrame.

    display_currency:
        기존 호출부와의 호환성을 위해 유지한다.
        Commission Rate는 비율이므로 통화 환산하지 않는다.

    language:
        Korean 또는 English.

    Notes
    -----
    Commission DataFrame의 PLAN(%), PQ(%), CQ(%) 값은
    이미 퍼센트 단위이다.

    CQ-PQ와 CQ-PLAN은 Percentage Point 단위이다.
    """
    del display_currency

    is_english = _is_english(language)

    lines: list[str] = []

    if is_english:
        lines.append(
            f"## 💰 Commission Rate Analysis – {target_ch}\n"
        )
    else:
        lines.append(
            f"## 💰 Commission Rate 분석 – {target_ch}\n"
        )

    if df_comm.empty:
        lines.append(
            "⚠️ No commission data is available."
            if is_english
            else "⚠️ Commission 데이터가 없습니다."
        )

        return "\n".join(lines)

    def format_percent(
        value,
    ) -> str:
        """Commission Rate를 퍼센트로 표시한다."""
        try:
            return f"{float(value):.2f}%"
        except (
            TypeError,
            ValueError,
        ):
            return "-"

    def format_difference(
        value,
    ) -> str:
        """Commission Rate 차이를 Percentage Point로 표시한다."""
        try:
            return f"{float(value):+.2f}%p"
        except (
            TypeError,
            ValueError,
        ):
            return "-"

    product_column = next(
        (
            column
            for column in [
                "PRODUCT",
                "PLICD",
                "PROD_NAME_BASE",
            ]
            if column in df_comm.columns
        ),
        None,
    )

    # ════════════════════════════════════════════════════════════
    # 1. CQ Commission Rate Top 5
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 1) Top 5 Current-Quarter Commission Rates"
        if is_english
        else "### 1) 당분기 수수료율 상위 5개"
    )

    if (
        "CQ(%)" in df_comm.columns
        and product_column
    ):
        current_top_five = df_comm.nlargest(
            5,
            "CQ(%)",
        )

        for rank, (_, row) in enumerate(
            current_top_five.iterrows(),
            1,
        ):
            product_name = row.get(
                product_column,
                "?",
            )

            channel_name = row.get(
                "CHANNEL",
                "",
            )

            premium_term = row.get(
                "납기",
                "",
            )

            details: list[str] = []

            if channel_name:
                details.append(
                    str(channel_name)
                )

            if (
                premium_term is not None
                and str(premium_term).strip()
                and str(premium_term).lower() != "nan"
            ):
                if is_english:
                    details.append(
                        f"{premium_term}-year premium term"
                    )
                else:
                    details.append(
                        f"{premium_term}년납"
                    )

            extra_text = (
                " | " + " | ".join(details)
                if details
                else ""
            )

            if is_english:
                lines.append(
                    f"{rank}. **{product_name}**{extra_text}: "
                    f"Current {format_percent(row.get('CQ(%)', 0))} / "
                    f"Previous {format_percent(row.get('PQ(%)', 0))} / "
                    f"Plan {format_percent(row.get('PLAN(%)', 0))}"
                )
            else:
                lines.append(
                    f"{rank}. **{product_name}**{extra_text}: "
                    f"당분기 {format_percent(row.get('CQ(%)', 0))} / "
                    f"전분기 {format_percent(row.get('PQ(%)', 0))} / "
                    f"Plan {format_percent(row.get('PLAN(%)', 0))}"
                )

    else:
        lines.append(
            "- The required commission-rate columns are not available."
            if is_english
            else "- 수수료율 분석에 필요한 컬럼이 없습니다."
        )

    lines.append("")

    # ════════════════════════════════════════════════════════════
    # 2. Variance to Plan Top 5
    # ════════════════════════════════════════════════════════════
    lines.append(
        "### 2) Top 5 Variances to Plan by Absolute Value"
        if is_english
        else "### 2) Plan 대비 편차 상위 5개 (절대값 기준)"
    )

    if (
        "CQ-PLAN" in df_comm.columns
        and product_column
    ):
        largest_variances = df_comm.reindex(
            df_comm["CQ-PLAN"]
            .abs()
            .sort_values(ascending=False)
            .index
        ).head(5)

        for rank, (_, row) in enumerate(
            largest_variances.iterrows(),
            1,
        ):
            product_name = row.get(
                product_column,
                "?",
            )

            variance = row.get(
                "CQ-PLAN",
                0,
            )

            if is_english:
                variance_direction = (
                    "above Plan"
                    if variance > 0
                    else (
                        "below Plan"
                        if variance < 0
                        else "in line with Plan"
                    )
                )

                lines.append(
                    f"{rank}. **{product_name}**: "
                    f"Plan {format_percent(row.get('PLAN(%)', 0))} → "
                    f"Current {format_percent(row.get('CQ(%)', 0))} "
                    f"({format_difference(variance)}, "
                    f"{variance_direction})"
                )

            else:
                variance_direction = (
                    "Plan 초과"
                    if variance > 0
                    else (
                        "Plan 미달"
                        if variance < 0
                        else "Plan과 동일"
                    )
                )

                lines.append(
                    f"{rank}. **{product_name}**: "
                    f"Plan {format_percent(row.get('PLAN(%)', 0))} → "
                    f"당분기 {format_percent(row.get('CQ(%)', 0))} "
                    f"({format_difference(variance)}, "
                    f"{variance_direction})"
                )

    else:
        lines.append(
            "- Variance-to-Plan data is not available."
            if is_english
            else "- Plan 대비 편차 데이터가 없습니다."
        )

    lines.append("")

    return "\n".join(lines)

