"""
utils/charts_extra.py
─────────────────────
VNB Dashboard 보조 차트 모음.

모든 함수는 language 인수를 선택적으로 받는다.
기존 호출과의 호환성을 위해 기본값은 Korean이다.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from styles.theme import (
    PRIMARY,
    THIRD,
    SUPPORT,
    C_WHITE,
)


def _is_english(
    language: str | None,
) -> bool:
    """언어 값이 English인지 확인한다."""
    return str(language).strip().lower() in {
        "english",
        "en",
        "eng",
    }


def _label(
    language: str,
    korean: str,
    english: str,
) -> str:
    """언어에 따른 문구를 반환한다."""
    return (
        english
        if _is_english(language)
        else korean
    )


# ════════════════════════════════════════════════════════════════
# 공통 Layout
# ════════════════════════════════════════════════════════════════
def _apply_common_layout(
    fig: go.Figure,
    title: str,
    height: int = 380,
) -> go.Figure:
    """보조 차트 공통 Layout을 적용한다."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(
                size=15,
                color=PRIMARY[0],
                family="Arial",
            ),
        ),
        height=height,
        paper_bgcolor=C_WHITE,
        plot_bgcolor=C_WHITE,
        font=dict(
            color=PRIMARY[0],
            family="Arial",
        ),
        margin=dict(
            t=60,
            b=50,
            l=60,
            r=30,
        ),
        hoverlabel=dict(
            bgcolor=C_WHITE,
            bordercolor=PRIMARY[2],
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        tickfont=dict(size=11),
    )

    fig.update_yaxes(
        gridcolor=SUPPORT[7],
        zerolinecolor=SUPPORT[5],
        tickfont=dict(size=11),
    )

    return fig


# ════════════════════════════════════════════════════════════════
# 1. 채널별 VNB 기여도
# ════════════════════════════════════════════════════════════════
def channel_contribution_bar(
    comp_table: pd.DataFrame,
    language: str = "Korean",
) -> go.Figure:
    """채널별 VNB 변동 기여도를 가로 막대로 표시한다."""
    dataframe = comp_table.drop(
        index="TOTAL (Company)",
        errors="ignore",
    ).copy()

    if dataframe.empty:
        return go.Figure()

    dataframe = dataframe.sort_values(
        ("DIFF", "VNB")
    )

    colors = [
        THIRD[3]
        if value >= 0
        else PRIMARY[4]
        for value in dataframe[("DIFF", "VNB")]
    ]

    hover_label = _label(
        language,
        "VNB 변동",
        "VNB Difference",
    )

    figure = go.Figure(
        go.Bar(
            x=dataframe[("DIFF", "VNB")] / 1_000_000,
            y=dataframe.index,
            orientation="h",
            marker=dict(
                color=colors,
                line=dict(
                    color=PRIMARY[1],
                    width=0.5,
                ),
            ),
            hovertemplate=(
                f"<b>%{{y}}</b><br>"
                f"{hover_label}: %{{x:,.1f}}M"
                "<extra></extra>"
            ),
        )
    )

    figure.add_vline(
        x=0,
        line=dict(
            color=SUPPORT[3],
            width=1,
        ),
    )

    title = _label(
        language,
        "채널별 VNB 기여도 (전분기 대비)",
        "Channel VNB Contribution (vs Previous Quarter)",
    )

    x_axis_title = _label(
        language,
        "VNB 변동 (백만 단위)",
        "VNB Difference (Millions)",
    )

    figure = _apply_common_layout(
        figure,
        title,
        height=360,
    )

    figure.update_xaxes(
        title_text=x_axis_title
    )

    return figure


# ════════════════════════════════════════════════════════════════
# 2. 채널별 Margin 산점도
# ════════════════════════════════════════════════════════════════
def margin_scatter(
    comp_table: pd.DataFrame,
    language: str = "Korean",
) -> go.Figure:
    """채널별 전분기 및 당분기 Margin을 산점도로 비교한다."""
    dataframe = comp_table.drop(
        index="TOTAL (Company)",
        errors="ignore",
    ).copy()

    if dataframe.empty:
        return go.Figure()

    current_vnb_abs = dataframe[
        ("CURR", "VNB")
    ].abs()

    sizes = (
        current_vnb_abs
        / max(current_vnb_abs.max(), 1)
        * 40
        + 8
    )

    prev_label = _label(
        language,
        "전분기",
        "Previous",
    )

    curr_label = _label(
        language,
        "당분기",
        "Current",
    )

    colorbar_title = _label(
        language,
        "마진 변동(%p)",
        "Δ Margin (%p)",
    )

    figure = go.Figure(
        go.Scatter(
            x=dataframe[("PREV", "VNB%")],
            y=dataframe[("CURR", "VNB%")],
            mode="markers+text",
            text=dataframe.index,
            textposition="top center",
            textfont=dict(
                size=10,
                color=PRIMARY[0],
            ),
            marker=dict(
                size=sizes,
                color=dataframe[("DIFF", "VNB%")],
                colorscale=[
                    [0, PRIMARY[4]],
                    [0.5, C_WHITE],
                    [1, THIRD[3]],
                ],
                cmin=-max(
                    dataframe[
                        ("DIFF", "VNB%")
                    ].abs().max(),
                    0.1,
                ),
                cmax=max(
                    dataframe[
                        ("DIFF", "VNB%")
                    ].abs().max(),
                    0.1,
                ),
                line=dict(
                    color=PRIMARY[1],
                    width=1,
                ),
                showscale=True,
                colorbar=dict(
                    title=colorbar_title,
                    thickness=10,
                    len=0.7,
                ),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                f"{prev_label}: %{{x:.2f}}%<br>"
                f"{curr_label}: %{{y:.2f}}%"
                "<extra></extra>"
            ),
        )
    )

    lower_bound = min(
        dataframe[("PREV", "VNB%")].min(),
        dataframe[("CURR", "VNB%")].min(),
    ) - 0.5

    upper_bound = max(
        dataframe[("PREV", "VNB%")].max(),
        dataframe[("CURR", "VNB%")].max(),
    ) + 0.5

    figure.add_trace(
        go.Scatter(
            x=[
                lower_bound,
                upper_bound,
            ],
            y=[
                lower_bound,
                upper_bound,
            ],
            mode="lines",
            line=dict(
                color=SUPPORT[4],
                dash="dash",
                width=1,
            ),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    title = _label(
        language,
        "채널 Margin: 전분기 vs 당분기",
        "Channel Margin: Previous vs Current",
    )

    figure = _apply_common_layout(
        figure,
        title,
        height=400,
    )

    figure.update_xaxes(
        title_text=_label(
            language,
            "전분기 Margin (%)",
            "Previous Margin (%)",
        )
    )

    figure.update_yaxes(
        title_text=_label(
            language,
            "당분기 Margin (%)",
            "Current Margin (%)",
        )
    )

    return figure


# ════════════════════════════════════════════════════════════════
# 3. Mix 비교 그룹 막대
# ════════════════════════════════════════════════════════════════
def mix_compare_bar(
    mix_df: pd.DataFrame,
    dim_col: str,
    title: str,
    language: str = "Korean",
) -> go.Figure:
    """전분기와 당분기의 Mix를 비교한다."""
    if mix_df.empty:
        return go.Figure()

    dataframe = mix_df.sort_values(
        "Curr. Mix(%)",
        ascending=False,
    )

    prev_name = _label(
        language,
        "전분기",
        "Previous Quarter",
    )

    curr_name = _label(
        language,
        "당분기",
        "Current Quarter",
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=dataframe[dim_col],
            y=dataframe["Prev. Mix(%)"],
            name=prev_name,
            marker=dict(
                color=SUPPORT[5],
                line=dict(
                    color=SUPPORT[2],
                    width=0.5,
                ),
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"{prev_name}: %{{y:.2f}}%"
                "<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Bar(
            x=dataframe[dim_col],
            y=dataframe["Curr. Mix(%)"],
            name=curr_name,
            marker=dict(
                color=PRIMARY[3],
                line=dict(
                    color=PRIMARY[1],
                    width=0.5,
                ),
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                f"{curr_name}: %{{y:.2f}}%"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        barmode="group",
        bargap=0.25,
        bargroupgap=0.05,
    )

    figure = _apply_common_layout(
        figure,
        title,
        height=380,
    )

    figure.update_yaxes(
        title_text="Mix (%)",
        ticksuffix="%",
    )

    figure.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        )
    )

    return figure


# ════════════════════════════════════════════════════════════════
# 4. 상품별 ANP 비중 변동
# ════════════════════════════════════════════════════════════════
def product_mix_diff_bar(
    comp_df: pd.DataFrame,
    name_col: str,
    title: str | None = None,
    diff_col: str = "Diff(%p)",
    prev_col: str = "Prev. Mix(%)",
    curr_col: str = "Curr. Mix(%)",
    top_n: int = 15,
    language: str = "Korean",
) -> go.Figure:
    """상품별 ANP 비중 변동을 Tornado 차트로 표시한다."""
    if (
        comp_df.empty
        or diff_col not in comp_df.columns
    ):
        return go.Figure()

    if title is None:
        title = _label(
            language,
            "상품별 ANP 비중 변동 (전분기 대비, %p)",
            "Change in ANP Mix by Product (vs Previous Quarter, %p)",
        )

    dataframe = comp_df.reindex(
        comp_df[diff_col]
        .abs()
        .sort_values(ascending=False)
        .index
    ).head(top_n)

    if dataframe.empty:
        return go.Figure()

    dataframe = dataframe.sort_values(
        diff_col
    )

    colors = [
        THIRD[3]
        if value >= 0
        else PRIMARY[4]
        for value in dataframe[diff_col]
    ]

    line_colors = [
        THIRD[1]
        if value >= 0
        else PRIMARY[1]
        for value in dataframe[diff_col]
    ]

    has_mix_columns = (
        prev_col in dataframe.columns
        and curr_col in dataframe.columns
    )

    custom_data = (
        dataframe[
            [
                prev_col,
                curr_col,
            ]
        ].to_numpy()
        if has_mix_columns
        else None
    )

    if has_mix_columns:
        hover_template = (
            "<b>%{y}</b><br>"
            + _label(
                language,
                "전분기 → 당분기",
                "Previous → Current",
            )
            + ": %{customdata[0].2f}% → %{customdata[1].2f}%"
            + "<br>"
            + _label(
                language,
                "변동",
                "Change",
            )
            + ": %{x:+.2f}%p"
            + "<extra></extra>"
        )
    else:
        hover_template = (
            "<b>%{y}</b><br>"
            + _label(
                language,
                "변동",
                "Change",
            )
            + ": %{x:+.2f}%p"
            + "<extra></extra>"
        )

    figure = go.Figure(
        go.Bar(
            x=dataframe[diff_col],
            y=dataframe[name_col].astype(str),
            orientation="h",
            text=[
                f"{value:+.2f}%p"
                for value in dataframe[diff_col]
            ],
            textposition="outside",
            marker=dict(
                color=colors,
                line=dict(
                    color=line_colors,
                    width=1.0,
                ),
            ),
            customdata=custom_data,
            hovertemplate=hover_template,
        )
    )

    figure.add_vline(
        x=0,
        line=dict(
            color=SUPPORT[3],
            width=1,
        ),
    )

    figure = _apply_common_layout(
        figure,
        title,
        height=max(
            320,
            26 * len(dataframe) + 100,
        ),
    )

    figure.update_xaxes(
        title_text=_label(
            language,
            "ANP 비중 변동 (%p)",
            "Change in ANP Mix (%p)",
        ),
        ticksuffix="%p",
    )

    return figure


# ════════════════════════════════════════════════════════════════
# 5. 상품 Growth 버블 차트
# ════════════════════════════════════════════════════════════════
def product_growth_bubble(
    prod_comp: pd.DataFrame,
    ts_comp: pd.DataFrame,
    language: str = "Korean",
) -> go.Figure:
    """상품 Mix 변화와 Ticket Size 변화를 버블 차트로 표시한다."""
    if (
        prod_comp.empty
        or ts_comp.empty
    ):
        return go.Figure()

    dataframe = pd.merge(
        prod_comp[
            [
                "PRODUCT",
                "Curr. Mix(%)",
                "Diff(%p)",
            ]
        ],
        ts_comp[
            [
                "PRODUCT",
                "Growth(%)",
            ]
        ],
        on="PRODUCT",
        how="inner",
    ).dropna()

    if dataframe.empty:
        return go.Figure()

    sizes = (
        dataframe["Curr. Mix(%)"].clip(lower=0)
        / max(
            dataframe["Curr. Mix(%)"].max(),
            1,
        )
        * 50
        + 10
    )

    def _quadrant_color(
        mix_diff: float,
        ticket_growth: float,
    ) -> str:
        if (
            mix_diff >= 0
            and ticket_growth >= 0
        ):
            return THIRD[3]

        if (
            mix_diff >= 0
            and ticket_growth < 0
        ):
            return THIRD[6]

        if (
            mix_diff < 0
            and ticket_growth >= 0
        ):
            return PRIMARY[6]

        return PRIMARY[4]

    colors = [
        _quadrant_color(
            mix_diff,
            ticket_growth,
        )
        for mix_diff, ticket_growth in zip(
            dataframe["Diff(%p)"],
            dataframe["Growth(%)"],
        )
    ]

    figure = go.Figure(
        go.Scatter(
            x=dataframe["Diff(%p)"],
            y=dataframe["Growth(%)"],
            mode="markers+text",
            text=dataframe["PRODUCT"],
            textposition="top center",
            textfont=dict(
                size=10,
                color=PRIMARY[0],
            ),
            marker=dict(
                size=sizes,
                color=colors,
                line=dict(
                    color=PRIMARY[1],
                    width=1,
                ),
                opacity=0.85,
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                + _label(
                    language,
                    "Mix 변동",
                    "Mix Change",
                )
                + ": %{x:+.2f}%p<br>"
                + _label(
                    language,
                    "Ticket Size 변동",
                    "Ticket Size Change",
                )
                + ": %{y:+.2f}%"
                + "<extra></extra>"
            ),
        )
    )

    figure.add_vline(
        x=0,
        line=dict(
            color=SUPPORT[3],
            width=1,
            dash="dash",
        ),
    )

    figure.add_hline(
        y=0,
        line=dict(
            color=SUPPORT[3],
            width=1,
            dash="dash",
        ),
    )

    figure = _apply_common_layout(
        figure,
        _label(
            language,
            "상품 Growth Map (Mix 변동 × Ticket Size 변동)",
            "Product Growth Map (Mix Change × Ticket Size Change)",
        ),
        height=420,
    )

    figure.update_xaxes(
        title_text=_label(
            language,
            "Mix 변동 (%p)",
            "Mix Change (%p)",
        ),
        ticksuffix="%p",
    )

    figure.update_yaxes(
        title_text=_label(
            language,
            "Ticket Size 증가율 (%)",
            "Ticket Size Growth (%)",
        ),
        ticksuffix="%",
    )

    return figure


# ════════════════════════════════════════════════════════════════
# 6. 연령 × 납기 Heatmap
# ════════════════════════════════════════════════════════════════
def age_term_heatmap(
    df_mpf: pd.DataFrame,
    title: str,
    language: str = "Korean",
) -> go.Figure | None:
    """연령대와 납입기간 조합을 ANP 비중 Heatmap으로 표시한다."""
    required_columns = {
        "AGE",
        "PREM_TERM",
        "ANP",
    }

    if (
        df_mpf.empty
        or not required_columns.issubset(df_mpf.columns)
    ):
        return None

    dataframe = df_mpf.copy()

    bins = [
        0,
        29,
        39,
        49,
        59,
        69,
        150,
    ]

    labels = (
        [
            "Under 30",
            "30s",
            "40s",
            "50s",
            "60s",
            "70 and Over",
        ]
        if _is_english(language)
        else [
            "30세 미만",
            "30대",
            "40대",
            "50대",
            "60대",
            "70세 이상",
        ]
    )

    dataframe["Age Group Display"] = pd.cut(
        dataframe["AGE"],
        bins=bins,
        labels=labels,
        right=True,
    )

    pivot = (
        dataframe.groupby(
            [
                "Age Group Display",
                "PREM_TERM",
            ],
            observed=True,
        )["ANP"]
        .sum()
        .reset_index()
        .pivot(
            index="Age Group Display",
            columns="PREM_TERM",
            values="ANP",
        )
        .fillna(0)
    )

    if pivot.empty:
        return None

    total = pivot.values.sum()

    if total <= 0:
        return None

    percentage = (
        pivot
        / total
        * 100
    )

    figure = go.Figure(
        go.Heatmap(
            z=percentage.values,
            x=[
                str(column)
                for column in percentage.columns
            ],
            y=[
                str(index)
                for index in percentage.index
            ],
            colorscale=[
                [0, C_WHITE],
                [0.5, PRIMARY[6]],
                [1, PRIMARY[1]],
            ],
            colorbar=dict(
                title="Mix (%)",
                thickness=10,
                len=0.8,
            ),
            hovertemplate=(
                _label(
                    language,
                    "연령대",
                    "Age Group",
                )
                + ": <b>%{y}</b><br>"
                + _label(
                    language,
                    "납입기간",
                    "Premium Term",
                )
                + ": <b>%{x}</b><br>"
                + "Mix: %{z:.2f}%"
                + "<extra></extra>"
            ),
        )
    )

    figure = _apply_common_layout(
        figure,
        title,
        height=380,
    )

    figure.update_xaxes(
        title_text=_label(
            language,
            "납입기간 (년)",
            "Premium Term (Years)",
        )
    )

    figure.update_yaxes(
        title_text=_label(
            language,
            "연령대",
            "Age Group",
        )
    )

    return figure


# ════════════════════════════════════════════════════════════════
# 7. Plan vs Actual
# ════════════════════════════════════════════════════════════════
def plan_vs_actual_bar(
    df: pd.DataFrame,
    label_col: str,
    plan_col: str,
    actual_col: str,
    title: str,
    language: str = "Korean",
) -> go.Figure:
    """Plan과 Actual을 비교한다."""
    if df.empty:
        return go.Figure()

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=df[label_col],
            y=df[plan_col],
            name="Plan",
            marker=dict(
                color=SUPPORT[5],
                line=dict(
                    color=SUPPORT[2],
                    width=0.5,
                ),
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Plan: %{y:,.1f}M"
                "<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Bar(
            x=df[label_col],
            y=df[actual_col],
            name="Actual",
            marker=dict(
                color=PRIMARY[3],
                line=dict(
                    color=PRIMARY[1],
                    width=0.5,
                ),
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Actual: %{y:,.1f}M"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        barmode="group",
        bargap=0.25,
        bargroupgap=0.05,
    )

    figure = _apply_common_layout(
        figure,
        title,
        height=360,
    )

    figure.update_yaxes(
        title_text=_label(
            language,
            "금액 (백만 단위)",
            "Amount (Millions)",
        )
    )

    figure.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        )
    )

    return figure


def _sort_distribution_values(
    dataframe: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """숫자 값을 먼저 정렬하고 기타 값을 마지막에 배치한다."""
    def _sort_key(value):
        try:
            return 0, float(str(value))
        except (TypeError, ValueError):
            return 1, 0

    return (
        dataframe.sort_values(
            column,
            key=lambda series: series.map(_sort_key),
        )
        .reset_index(drop=True)
    )


def _distribution_compare_bar(
    dataframe: pd.DataFrame,
    x_column: str,
    title: str,
    x_axis_title: str,
    language: str,
    hover_prefix: str = "",
) -> go.Figure:
    """전분기와 당분기 분포 비교 차트 공통 함수."""
    if dataframe.empty:
        return go.Figure()

    previous_name = _label(
        language,
        "전분기",
        "Previous Quarter",
    )

    current_name = _label(
        language,
        "당분기",
        "Current Quarter",
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=dataframe[x_column].astype(str),
            y=dataframe["Prev. Mix(%)"],
            name=previous_name,
            marker=dict(
                color=SUPPORT[5],
                line=dict(
                    color=SUPPORT[2],
                    width=0.8,
                ),
            ),
            hovertemplate=(
                f"<b>{hover_prefix}%{{x}}</b><br>"
                f"{previous_name}: %{{y:.2f}}%"
                "<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Bar(
            x=dataframe[x_column].astype(str),
            y=dataframe["Curr. Mix(%)"],
            name=current_name,
            marker=dict(
                color=PRIMARY[3],
                line=dict(
                    color=PRIMARY[1],
                    width=0.8,
                ),
            ),
            hovertemplate=(
                f"<b>{hover_prefix}%{{x}}</b><br>"
                f"{current_name}: %{{y:.2f}}%"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        barmode="group",
        bargap=0.28,
        bargroupgap=0.06,
    )

    figure = _apply_common_layout(
        figure,
        title,
        height=360,
    )

    figure.update_xaxes(
        title_text=x_axis_title
    )

    figure.update_yaxes(
        title_text="Mix (%)",
        ticksuffix="%",
    )

    figure.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        )
    )

    return figure


# ════════════════════════════════════════════════════════════════
# 8. 납입기간 분포
# ════════════════════════════════════════════════════════════════
def term_compare_bar(
    term_comp: pd.DataFrame,
    title: str | None = None,
    language: str = "Korean",
) -> go.Figure:
    """납입기간별 ANP Mix를 비교한다."""
    if term_comp.empty:
        return go.Figure()

    if title is None:
        title = _label(
            language,
            "납입기간 분포 · 전분기 vs 당분기",
            "Premium Term Distribution · Previous vs Current",
        )

    dataframe = _sort_distribution_values(
        term_comp.copy(),
        "Term",
    )

    hover_prefix = (
        ""
        if _is_english(language)
        else ""
    )

    return _distribution_compare_bar(
        dataframe,
        x_column="Term",
        title=title,
        x_axis_title=_label(
            language,
            "납입기간 (년)",
            "Premium Term (Years)",
        ),
        language=language,
        hover_prefix=hover_prefix,
    )


# ════════════════════════════════════════════════════════════════
# 9. 거치기간 분포
# ════════════════════════════════════════════════════════════════
def defer_compare_bar(
    defer_comp: pd.DataFrame,
    title: str | None = None,
    language: str = "Korean",
) -> go.Figure:
    """거치기간별 ANP Mix를 비교한다."""
    if defer_comp.empty:
        return go.Figure()

    if title is None:
        title = _label(
            language,
            "거치기간 분포 · 전분기 vs 당분기",
            "Deferment Period Distribution · Previous vs Current",
        )

    dataframe = _sort_distribution_values(
        defer_comp.copy(),
        "DEFER_Y",
    )

    return _distribution_compare_bar(
        dataframe,
        x_column="DEFER_Y",
        title=title,
        x_axis_title=_label(
            language,
            "거치기간 (년)",
            "Deferment Period (Years)",
        ),
        language=language,
        hover_prefix=_label(
            language,
            "거치 ",
            "",
        ),
    )


# ════════════════════════════════════════════════════════════════
# 10. 연령대 분포
# ════════════════════════════════════════════════════════════════
def age_compare_bar(
    age_comp: pd.DataFrame,
    title: str | None = None,
    language: str = "Korean",
) -> go.Figure:
    """연령대별 ANP Mix를 비교한다."""
    if age_comp.empty:
        return go.Figure()

    if title is None:
        title = _label(
            language,
            "연령대 분포 · 전분기 vs 당분기",
            "Age Group Distribution · Previous vs Current",
        )

    age_order = [
        "Under 30",
        "30s",
        "40s",
        "50s",
        "60s",
        "Over 70",
    ]

    dataframe = age_comp.copy()

    dataframe["_order"] = (
        dataframe["Age Group"]
        .map({
            group: index
            for index, group in enumerate(age_order)
        })
        .fillna(99)
    )

    dataframe = (
        dataframe
        .sort_values("_order")
        .drop(columns="_order")
        .reset_index(drop=True)
    )

    display_labels = dataframe[
        "Age Group"
    ].astype(str)

    if not _is_english(language):
        age_label_map = {
            "Under 30": "30세 미만",
            "30s": "30대",
            "40s": "40대",
            "50s": "50대",
            "60s": "60대",
            "Over 70": "70세 이상",
        }

        display_labels = display_labels.map(
            lambda value: age_label_map.get(
                value,
                value,
            )
        )

    chart_dataframe = dataframe.copy()
    chart_dataframe["Age Group Display"] = display_labels

    return _distribution_compare_bar(
        chart_dataframe,
        x_column="Age Group Display",
        title=title,
        x_axis_title=_label(
            language,
            "연령대",
            "Age Group",
        ),
        language=language,
    )