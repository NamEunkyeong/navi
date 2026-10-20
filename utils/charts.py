"""
utils/charts.py
───────────────
VNB Walk Waterfall 차트 및 Step Impact 계산.

차트에 표시되는 제목, 축, Hover 문구는 language 인수를 통해
Korean / English로 전환한다.

measure 규칙
------------
PQ:
    absolute

CQ:
    total

기타 Step:
    relative
"""

from __future__ import annotations

import plotly.graph_objects as go

from styles.theme import PRIMARY, THIRD, SUPPORT, C_WHITE


_COLOR_INC = THIRD[6]
_COLOR_INC_LINE = THIRD[6]
_COLOR_DEC = PRIMARY[8]
_COLOR_DEC_LINE = PRIMARY[8]
_COLOR_TOTAL = PRIMARY[0]
_COLOR_CONN = SUPPORT[6]
_COLOR_GRID = SUPPORT[8]
_COLOR_TEXT = PRIMARY[0]

_MILLION = 1_000_000


def _is_english(language: str | None) -> bool:
    """언어 값이 English인지 확인한다."""
    return str(language).strip().lower() in {
        "english",
        "en",
        "eng",
    }


def _fmt_m(
    val: float,
    display_currency: str,
    unit_suffix: str,
) -> str:
    """Waterfall 차트의 금액 라벨을 Millions 단위로 포맷한다."""
    value_in_millions = val / _MILLION

    if display_currency == "USD":
        return f"{unit_suffix}{value_in_millions:,.2f}M"

    return f"{unit_suffix}{value_in_millions:,.1f}M"


def compute_step_impacts(
    df,
    step_order: list,
    ct_pq_anp: float = 0.0,
    ct_cq_anp: float = 0.0,
) -> dict:
    """
    Step별 delta amount와 Margin Impact(%p)를 계산한다.

    Returns
    -------
    dict
        {
            step_name: (
                delta_amount,
                margin_impact_percentage_point,
            )
        }
    """
    step_agg = (
        df.groupby("STEP")
        .agg({
            "VNB": "sum",
            "ANP": "sum",
        })
        .reindex(step_order)
        .fillna(0)
    )

    pq_anp = (
        float(step_agg.loc["PQ", "ANP"])
        if "PQ" in step_agg.index
        else 0.0
    )

    cq_anp = (
        float(step_agg.loc["CQ", "ANP"])
        if "CQ" in step_agg.index
        else 0.0
    )

    sl_vol_ratio = (
        ct_cq_anp / ct_pq_anp
        if ct_pq_anp
        else 1.0
    )

    pq_anp_steps = {
        "PQ",
        "PQ_TVOG",
        "PQ_ETU",
        "PQ_COMM",
    }

    sl_vol_step = "SL_VOL"

    sl_mix_index = (
        step_order.index("SL_MIX")
        if "SL_MIX" in step_order
        else len(step_order)
    )

    cq_anp_steps = set(
        step_order[sl_mix_index:]
    )

    output: dict = {}

    running_vnb = 0.0
    running_margin = 0.0

    for step, row in step_agg.iterrows():
        vnb_value = float(row["VNB"])

        if step in pq_anp_steps:
            anp_value = pq_anp

        elif step == sl_vol_step:
            anp_value = (
                pq_anp
                * sl_vol_ratio
            )

        elif step in cq_anp_steps:
            anp_value = cq_anp

        else:
            anp_value = pq_anp

        if step == "PQ":
            delta = vnb_value
            running_vnb = delta

            margin_now = (
                vnb_value / anp_value * 100
                if anp_value
                else 0.0
            )

            margin_impact = margin_now

        elif step == "CQ":
            delta = vnb_value

            margin_now = (
                vnb_value / anp_value * 100
                if anp_value
                else 0.0
            )

            margin_impact = margin_now

        else:
            delta = (
                vnb_value
                - running_vnb
            )

            running_vnb = vnb_value

            if step == sl_vol_step:
                # SL_VOL은 정의상 Margin 변화가 없는 가상 Volume Step이다.
                margin_now = running_margin

            else:
                margin_now = (
                    vnb_value / anp_value * 100
                    if anp_value
                    else 0.0
                )

            margin_impact = (
                margin_now
                - running_margin
            )

        running_margin = margin_now

        output[step] = (
            float(delta),
            float(margin_impact),
        )

    return output


def create_waterfall_chart(
    df,
    title: str,
    step_order: list,
    display_currency: str,
    unit_suffix: str,
    ct_pq_anp: float = 0.0,
    ct_cq_anp: float = 0.0,
    language: str = "Korean",
) -> go.Figure:
    """
    VNB Walk Waterfall 차트를 생성한다.

    Parameters
    ----------
    language:
        Korean 또는 English.
    """
    is_english = _is_english(language)

    step_agg = (
        df.groupby("STEP")
        .agg({
            "VNB": "sum",
            "ANP": "sum",
        })
        .reindex(step_order)
        .fillna(0)
    )

    impacts = compute_step_impacts(
        df,
        step_order,
        ct_pq_anp,
        ct_cq_anp,
    )

    x_values: list[str] = []
    y_values: list[float] = []
    measures: list[str] = []
    text_labels: list[str] = []
    hover_labels: list[str] = []

    running_value = 0.0

    for step, row in step_agg.iterrows():
        vnb_value = float(row["VNB"])
        delta, margin_impact = impacts[step]

        if step == "PQ":
            measure = "absolute"

            label = _fmt_m(
                delta,
                display_currency,
                unit_suffix,
            )

            label += (
                f"<br>({margin_impact:.2f}%)"
            )

            running_value = delta

            hover_text = (
                f"<b>{step}</b><br>"
                f"{'VNB Amount' if is_english else 'VNB 금액'}: "
                f"{_fmt_m(delta, display_currency, unit_suffix)}<br>"
                f"{'Margin' if is_english else '마진'}: "
                f"{margin_impact:.2f}%"
            )

        elif step == "CQ":
            measure = "total"
            running_value = delta

            label = (
                f"<b>{_fmt_m(running_value, display_currency, unit_suffix)}</b>"
                f"<br>({margin_impact:.2f}%)"
            )

            hover_text = (
                f"<b>{step}</b><br>"
                f"{'VNB Amount' if is_english else 'VNB 금액'}: "
                f"{_fmt_m(running_value, display_currency, unit_suffix)}<br>"
                f"{'Margin' if is_english else '마진'}: "
                f"{margin_impact:.2f}%"
            )

        else:
            running_value = vnb_value
            measure = "relative"

            sign = (
                "+"
                if delta >= 0
                else ""
            )

            label = (
                sign
                + _fmt_m(
                    delta,
                    display_currency,
                    unit_suffix,
                )
            )

            label += (
                f"<br>({margin_impact:+.2f}%p)"
            )

            hover_text = (
                f"<b>{step}</b><br>"
                f"{'VNB Impact' if is_english else 'VNB 영향'}: "
                f"{_fmt_m(delta, display_currency, unit_suffix)}<br>"
                f"{'Margin Impact' if is_english else '마진 영향'}: "
                f"{margin_impact:+.2f}%p"
            )

        x_values.append(step)
        y_values.append(delta)
        measures.append(measure)
        text_labels.append(label)
        hover_labels.append(hover_text)

    figure = go.Figure(
        go.Waterfall(
            x=x_values,
            y=y_values,
            text=text_labels,
            customdata=hover_labels,
            hovertemplate="%{customdata}<extra></extra>",
            textposition="outside",
            textfont=dict(
                size=11,
                color=_COLOR_TEXT,
            ),
            measure=measures,
            increasing=dict(
                marker=dict(
                    color=_COLOR_INC,
                    line=dict(
                        color=_COLOR_INC_LINE,
                        width=1.5,
                    ),
                )
            ),
            decreasing=dict(
                marker=dict(
                    color=_COLOR_DEC,
                    line=dict(
                        color=_COLOR_DEC_LINE,
                        width=1.5,
                    ),
                )
            ),
            totals=dict(
                marker=dict(
                    color=_COLOR_TOTAL,
                    line=dict(
                        color=PRIMARY[0],
                        width=1.5,
                    ),
                )
            ),
            connector=dict(
                line=dict(
                    color=_COLOR_CONN,
                    width=1,
                    dash="dot",
                )
            ),
        )
    )

    running_level = 0.0
    levels = [0.0]

    for step, value in zip(
        x_values,
        y_values,
    ):
        if step in {
            "PQ",
            "CQ",
        }:
            running_level = value
        else:
            running_level += value

        levels.append(running_level)

    max_level = max(levels)
    min_level = min(levels)

    span = (
        max_level - min_level
    ) or (
        abs(max_level)
        if max_level
        else 1.0
    )

    y_range = [
        min_level - span * 0.10,
        max_level + span * 0.22,
    ]

    y_axis_title = (
        f"VNB ({display_currency}, Millions)"
        if is_english
        else f"VNB ({display_currency}, 백만 단위)"
    )

    figure.update_layout(
        title=dict(
            text=title,
            font=dict(
                size=18,
                color=_COLOR_TEXT,
                family="Arial Black",
            ),
        ),
        height=520,
        paper_bgcolor=C_WHITE,
        plot_bgcolor=C_WHITE,
        font=dict(
            color=_COLOR_TEXT,
            family="Arial",
        ),
        hoverlabel=dict(
            bgcolor=C_WHITE,
            bordercolor=PRIMARY[2],
        ),
        bargap=0.35,
        margin=dict(
            t=80,
            b=60,
            l=80,
            r=40,
        ),
        showlegend=False,
        yaxis=dict(
            title=dict(
                text=y_axis_title,
                font=dict(size=13),
            ),
            gridcolor=_COLOR_GRID,
            zerolinecolor=SUPPORT[5],
            zerolinewidth=1.5,
            tickfont=dict(size=11),
            tickformat=".3s",
            range=y_range,
        ),
        xaxis=dict(
            tickfont=dict(
                size=12,
                color=_COLOR_TEXT,
            ),
            showgrid=False,
        ),
    )

    return figure