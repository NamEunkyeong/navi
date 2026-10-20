"""
utils/io/vnb.py — VNB(vnb.parquet) 필터링 헬퍼.

SCEN=="MR" 기준 EXPTU/TVOG 인덱스 슬라이스(get_vnb_cq)와, 전분기 VNB에서
PQ/PQ_TVOG/PQ_ETU 3-step을 뽑아내는 walk prefix 계산(_build_walk_prefix_from_df)을 담당한다.
"""
from __future__ import annotations

import pandas as pd

from .config import quarter_end_date


def _vnb_slice(
    df: pd.DataFrame,
    exptu: int,
    tvog: int,
    date_str: str | None = None,
) -> pd.DataFrame:
    """
    SCEN=='MR' & EXPTU_IDX==exptu & TVOG_IDX==tvog 필터.
    date_str 지정 시 DATE 컬럼도 함께 필터.
    """
    if df.empty:
        return df
    scen_col = "SCEN" if "SCEN" in df.columns else "SCENARIO"
    mask = (
        (df[scen_col] == "MR") &
        (df["EXPTU_IDX"] == exptu) &
        (df["TVOG_IDX"]  == tvog)
    )
    if date_str is not None and "DATE" in df.columns:
        mask = mask & (df["DATE"].astype(str) == date_str)
    return df.loc[mask].copy()


def get_vnb_cq(
    df: pd.DataFrame,
    date_str: str | None = None,
    channel: str = "Company Total",
    product_group: str = "Company Total",
    product: str = "All",
) -> pd.DataFrame:
    """CQ: SCEN=MR, EXPTU=1, TVOG=1. date_str / channel / product_group / product 필터 가능."""
    result = _vnb_slice(df, 1, 1, date_str)
    if not result.empty:
        if channel != "Company Total" and "CHANNEL" in result.columns:
            result = result[result["CHANNEL"] == channel]
        if product_group != "Company Total" and "PRODUCT_GROUP1" in result.columns:
            result = result[result["PRODUCT_GROUP1"] == product_group]
        if product != "All" and "PRODUCT" in result.columns:
            result = result[result["PRODUCT"] == product]
    return result


# ════════════════════════════════════════════════════════════════
# Walk prefix (VNB prev에서 PQ/PQ_TVOG/PQ_ETU 추출. PQ_COMM은 df_walk_file에 이미 있음)
# ════════════════════════════════════════════════════════════════
def _build_walk_prefix_from_df(
    df: pd.DataFrame,
    py: int,
    pq: str,
    channel: str = "Company Total",
    product_group: str = "Company Total",
    product: str = "All",
) -> pd.DataFrame:
    """
    전분기 VNB df → PQ / PQ_TVOG / PQ_ETU 3 step 추출.
    channel / product_group / product 필터 지원. VNB는 절대값으로 저장.

    PQ_COMM은 여기서 만들지 않는다 — vnb-walk.parquet(df_walk_file) 안에
    이미 STEP="PQ_COMM" 행으로 존재하므로, load_all_data()에서
    prefix + df_walk_file을 concat할 때 자연히 포함된다.
    """
    if df.empty:
        return pd.DataFrame(columns=["STEP", "VNB", "ANP"])

    end_date  = quarter_end_date(py, pq)
    scen_col  = "SCEN" if "SCEN" in df.columns else "SCENARIO"
    date_mask = df["DATE"].astype(str) == end_date
    ch_mask   = (df["CHANNEL"] == channel) if (channel != "Company Total" and "CHANNEL" in df.columns) else pd.Series(True, index=df.index)
    pg_mask   = (df["PRODUCT_GROUP1"] == product_group) if (product_group != "Company Total" and "PRODUCT_GROUP1" in df.columns) else pd.Series(True, index=df.index)
    prod_mask = (df["PRODUCT"] == product) if (product != "All" and "PRODUCT" in df.columns) else pd.Series(True, index=df.index)
    base_mask = date_mask & ch_mask & pg_mask & prod_mask & (df[scen_col] == "MR")

    def _s(exptu, tvog, col="VNB"):
        mask = base_mask & (df["EXPTU_IDX"] == exptu) & (df["TVOG_IDX"] == tvog)
        return float(df.loc[mask, col].sum()) if mask.any() else 0.0

    pq_vnb   = _s(1, 1)
    tvog_vnb = _s(1, 0)
    etu_vnb  = _s(0, 0)
    pq_anp   = _s(1, 1, "ANP")

    return pd.DataFrame([
        {"STEP": "PQ",      "VNB": pq_vnb,   "ANP": pq_anp},
        {"STEP": "PQ_TVOG", "VNB": tvog_vnb, "ANP": pq_anp},
        {"STEP": "PQ_ETU",  "VNB": etu_vnb,  "ANP": pq_anp},
    ])
