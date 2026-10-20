"""
utils/tables.py
───────────────
DataFrame 집계 및 Streamlit 표 렌더링 함수.

계산용 내부 컬럼명과 인덱스는 기존 값을 그대로 유지하고,
사용자에게 표시되는 캡션만 Korean / English로 전환한다.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd
import streamlit as st

from styles.theme import PRIMARY, THIRD
from utils.util import MILLION


Translator = Callable[..., str]


# ════════════════════════════════════════════════════════════════
# 표 단위 캡션
# ════════════════════════════════════════════════════════════════
def _unit_caption(
    display_currency: str,
    t: Translator | None = None,
) -> str:
    """통화별 단위 캡션을 반환한다."""
    symbol = (
        "$"
        if display_currency == "USD"
        else "₩"
    )

    if t is not None:
        return t(
            "unit_millions",
            symbol=symbol,
        )

    return f"Unit: Millions ({symbol}M)"


# ════════════════════════════════════════════════════════════════
# Summary 집계 표
# ════════════════════════════════════════════════════════════════
def get_summary_table(
    key: str,
    df_p: pd.DataFrame,
    df_c: pd.DataFrame,
) -> pd.DataFrame:
    """
    지정 차원별 ANP, VNB, VNB Margin 비교 테이블을 생성한다.

    MultiIndex 컬럼
    ----------------
    PREV / CURR / DIFF × ANP / VNB / VNB%
    """
    if (
        df_c.empty
        or key not in df_c.columns
    ):
        multi_index = pd.MultiIndex.from_arrays([
            [
                "PREV",
                "PREV",
                "PREV",
                "CURR",
                "CURR",
                "CURR",
                "DIFF",
                "DIFF",
                "DIFF",
            ],
            [
                "ANP",
                "VNB",
                "VNB%",
                "ANP",
                "VNB",
                "VNB%",
                "ANP",
                "VNB",
                "VNB%",
            ],
        ])

        return pd.DataFrame(
            columns=multi_index,
        )

    def _aggregate(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        if (
            dataframe.empty
            or key not in dataframe.columns
        ):
            return pd.DataFrame(
                columns=[
                    "ANP",
                    "VNB",
                    "VNB%",
                ]
            )

        grouped = dataframe.groupby(key)[
            [
                "ANP",
                "VNB",
            ]
        ].sum()

        total = (
            pd.DataFrame(grouped.sum())
            .T
            .rename(index={0: "TOTAL (Company)"})
        )

        output = pd.concat([
            total,
            grouped,
        ])

        output["VNB%"] = (
            output["VNB"]
            / output["ANP"]
            * 100
        ).replace(
            [
                float("inf"),
                float("-inf"),
            ],
            0,
        ).fillna(0)

        return output

    curr = _aggregate(df_c)

    if not df_p.empty:
        prev = _aggregate(df_p)
    else:
        prev = pd.DataFrame(
            0,
            index=curr.index,
            columns=[
                "ANP",
                "VNB",
                "VNB%",
            ],
        )

    index = curr.index.union(prev.index)

    curr = curr.reindex(
        index,
        fill_value=0,
    )

    prev = prev.reindex(
        index,
        fill_value=0,
    )

    multi_index = pd.MultiIndex.from_arrays([
        [
            "PREV",
            "PREV",
            "PREV",
            "CURR",
            "CURR",
            "CURR",
            "DIFF",
            "DIFF",
            "DIFF",
        ],
        [
            "ANP",
            "VNB",
            "VNB%",
            "ANP",
            "VNB",
            "VNB%",
            "ANP",
            "VNB",
            "VNB%",
        ],
    ])

    return pd.DataFrame(
        {
            ("PREV", "ANP"): prev["ANP"],
            ("PREV", "VNB"): prev["VNB"],
            ("PREV", "VNB%"): prev["VNB%"],
            ("CURR", "ANP"): curr["ANP"],
            ("CURR", "VNB"): curr["VNB"],
            ("CURR", "VNB%"): curr["VNB%"],
            ("DIFF", "ANP"): (
                curr["ANP"]
                - prev["ANP"]
            ),
            ("DIFF", "VNB"): (
                curr["VNB"]
                - prev["VNB"]
            ),
            ("DIFF", "VNB%"): (
                curr["VNB%"]
                - prev["VNB%"]
            ),
        },
        index=index,
        columns=multi_index,
    )


# ════════════════════════════════════════════════════════════════
# Step 상세 표 계산
# ════════════════════════════════════════════════════════════════
def build_step_detail_table(
    filtered_df: pd.DataFrame,
    step_order: list,
    ct_pq_anp: float = 0.0,
    ct_cq_anp: float = 0.0,
) -> pd.DataFrame:
    """
    Step별 ANP, VNB, VNB Margin 상세표를 생성한다.

    반환 값은 이미 Millions 단위로 변환된다.
    """
    step_agg = (
        filtered_df.groupby("STEP")[
            [
                "ANP",
                "VNB",
            ]
        ]
        .sum()
        .reindex(step_order)
        .fillna(0)
    )

    pq_anp_steps = {
        "PQ",
        "PQ_TVOG",
        "PQ_ETU",
        "PQ_COMM",
    }

    sl_vol_step = "SL_VOL"

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

    sl_mix_index = (
        step_order.index("SL_MIX")
        if "SL_MIX" in step_order
        else len(step_order)
    )

    cq_anp_steps = set(
        step_order[sl_mix_index:]
    )

    anp_row: dict[str, float] = {}

    for step in step_order:
        if step in pq_anp_steps:
            anp_row[step] = pq_anp

        elif step == sl_vol_step:
            anp_row[step] = (
                pq_anp
                * sl_vol_ratio
            )

        elif step in cq_anp_steps:
            anp_row[step] = cq_anp

        else:
            anp_row[step] = pq_anp

    vnb_row = {
        step: (
            float(step_agg.loc[step, "VNB"])
            if step in step_agg.index
            else 0.0
        )
        for step in step_order
    }

    step_data = pd.DataFrame(
        {
            "ANP": anp_row,
            "VNB": vnb_row,
        },
        index=step_order,
    ).T

    step_data.loc["ANP"] /= MILLION
    step_data.loc["VNB"] /= MILLION

    step_data.loc["VNB%"] = (
        step_data.loc["VNB"]
        / step_data.loc["ANP"].replace(
            0,
            float("nan"),
        )
        * 100
    ).fillna(0)

    # SL_VOL은 정의상 Margin이 변하지 않는 가상 볼륨 Step이다.
    if sl_vol_step in step_data.columns:
        sl_vol_position = step_order.index(
            sl_vol_step
        )

        if sl_vol_position > 0:
            previous_step = step_order[
                sl_vol_position - 1
            ]

            if previous_step in step_data.columns:
                previous_margin = step_data.loc[
                    "VNB%",
                    previous_step,
                ]

                step_data.loc[
                    "VNB%",
                    sl_vol_step,
                ] = previous_margin

                if previous_margin:
                    sl_vol_vnb = step_data.loc[
                        "VNB",
                        sl_vol_step,
                    ]

                    step_data.loc[
                        "ANP",
                        sl_vol_step,
                    ] = (
                        sl_vol_vnb
                        / (previous_margin / 100)
                    )

    return step_data


# ════════════════════════════════════════════════════════════════
# Step 상세 표 렌더링
# ════════════════════════════════════════════════════════════════
def render_step_detail_table(
    filtered_df: pd.DataFrame,
    step_order: list,
    display_currency: str,
    ct_pq_anp: float = 0.0,
    ct_cq_anp: float = 0.0,
    t: Translator | None = None,
) -> pd.DataFrame:
    """
    Step별 상세표를 Streamlit에 표시하고 DataFrame을 반환한다.

    반환된 DataFrame은 HTML Export에도 그대로 활용할 수 있다.
    """
    step_data = build_step_detail_table(
        filtered_df,
        step_order,
        ct_pq_anp=ct_pq_anp,
        ct_cq_anp=ct_cq_anp,
    )

    table_styles = [
        {
            "selector": "th",
            "props": [
                ("text-align", "center"),
            ],
        }
    ]

    st.caption(
        _unit_caption(
            display_currency,
            t=t,
        )
    )

    st.dataframe(
        step_data.style
        .format(
            formatter="{:,.1f}",
            subset=pd.IndexSlice[
                [
                    "ANP",
                    "VNB",
                ],
                :,
            ],
        )
        .format(
            formatter="{:.2f}%",
            subset=pd.IndexSlice[
                ["VNB%"],
                :,
            ],
        )
        .set_table_styles(table_styles),
        width="stretch",
    )

    return step_data


# ════════════════════════════════════════════════════════════════
# Top-N 하이라이트
# ════════════════════════════════════════════════════════════════
def highlight_top_abs_diff(
    df: pd.DataFrame,
    diff_col: str = "Diff(%p)",
    top_n: int = 4,
    bg_color: str | None = None,
):
    """
    diff_col 절대값 기준 상위 top_n 행에 배경색을 적용한다.
    """
    if bg_color is None:
        bg_color = THIRD[8] + "B3"

    abs_series = (
        pd.to_numeric(
            df[diff_col],
            errors="coerce",
        )
        .abs()
        .fillna(0)
    )

    top_indices = (
        abs_series
        .nlargest(top_n)
        .index
    )

    def _style(
        row: pd.Series,
    ) -> list:
        if row.name in top_indices:
            style = (
                f"background-color: {bg_color}; "
                f"border-left: 3px solid {PRIMARY[3]};"
            )

            return [style] * len(row)

        return [""] * len(row)

    return _style