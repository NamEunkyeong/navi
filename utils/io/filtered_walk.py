"""
utils/io/filtered_walk.py — 채널/상품군/상품 필터를 반영한 VNB Walk 동적 생성.

Sales Mix / Demo 탭에서 필터가 바뀔 때마다 호출되며, dashboard.py의
_cached_filtered_walk()가 이 함수 결과를 캐시한다.
"""
from __future__ import annotations

import pandas as pd

from .config import prev_quarter, quarter_end_date
from .vnb import _build_walk_prefix_from_df, get_vnb_cq


def build_filtered_walk(
    df_vnb_prev_full: "pd.DataFrame",
    df_vnb_curr_full: "pd.DataFrame",
    df_walk_file: "pd.DataFrame",
    year: int,
    quarter: str,
    channel: str = "Company Total",
    product_group: str = "Company Total",
    product: str = "All",
    fx_rate: float = 1.0,
    display_currency: str = "KRW",
) -> "pd.DataFrame":
    """
    채널/상품군/상품 필터를 반영한 VNB Walk DataFrame 동적 생성.
    PQ/PQ_TVOG/PQ_ETU → 전분기 vnb.parquet에서 필터 후 집계 (PQ_COMM은 walk.parquet에 이미 있음)
    walk steps        → walk.parquet 필터
    CQ_TVOG/CQ        → 당분기 vnb.parquet에서 필터 후 집계
    """
    py, pq_str = prev_quarter(year, quarter)
    curr_end   = quarter_end_date(year, quarter)

    prefix = _build_walk_prefix_from_df(
        df_vnb_prev_full, py, pq_str,
        channel=channel, product_group=product_group, product=product,
    )

    _FIXED = {"PQ", "PQ_TVOG", "PQ_ETU", "CQ_TVOG", "CQ"}
    walk_f = df_walk_file.copy()
    if channel != "Company Total" and "CHANNEL" in walk_f.columns:
        walk_f = walk_f[walk_f["CHANNEL"] == channel]
    if product_group != "Company Total" and "PRODUCT_GROUP1" in walk_f.columns:
        walk_f = walk_f[walk_f["PRODUCT_GROUP1"] == product_group]
    if product != "All" and "PRODUCT" in walk_f.columns:
        walk_f = walk_f[walk_f["PRODUCT"] == product]
    if "STEP" in walk_f.columns:
        walk_f = walk_f[~walk_f["STEP"].isin(_FIXED)]

    cq_df  = get_vnb_cq(df_vnb_curr_full, curr_end, channel=channel, product_group=product_group, product=product)
    cq_vnb = float(cq_df["VNB"].sum()) if not cq_df.empty else 0.0
    cq_anp = float(cq_df["ANP"].sum()) if not cq_df.empty else 0.0

    combined = pd.concat([
        prefix,
        walk_f,
        pd.DataFrame([{"STEP": "CQ_TVOG", "VNB": cq_vnb, "ANP": cq_anp}]),
        pd.DataFrame([{"STEP": "CQ",       "VNB": cq_vnb, "ANP": cq_anp}]),
    ], ignore_index=True)

    if display_currency == "USD" and fx_rate and fx_rate != 1.0:
        combined["VNB"] = combined["VNB"] / fx_rate
        combined["ANP"] = combined["ANP"] / fx_rate

    return combined
