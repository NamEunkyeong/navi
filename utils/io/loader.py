"""
utils/io/loader.py — 메인 데이터 로더.

VNB/MPF/Commission/Expense 원본 파일을 모두 읽어 dashboard.py가 바로 쓸 수
있는 형태로 조립한다(load_all_data). 캐시 무효화 키 계산은 _paths_mtime.
"""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from .commission import load_commission_data
from .config import prev_quarter, quarter_end_date
from .mpf import _MPF_FILES, _load_mpf_dir
from .vnb import _build_walk_prefix_from_df, get_vnb_cq


def _paths_mtime(paths: dict) -> str:
    """parquet 파일들의 수정 시간을 문자열로 반환 — 캐시 키용."""
    mtimes = []
    for key, fpath in paths.items():
        try:
            mtimes.append(f"{key}:{os.path.getmtime(fpath):.0f}")
        except (OSError, TypeError):
            mtimes.append(f"{key}:0")
    return "|".join(sorted(mtimes))


@st.cache_data
def load_all_data(year: int, quarter: str, paths: dict, _mtime: str = "") -> tuple:
    """_mtime은 캐시 무효화용 — 직접 넘기지 않고 wrapper에서 자동 계산."""
    """
    반환 순서 (v18):
    df_mpf_prev, df_mpf_curr,
    df_vnb_walk,            ← PQ prefix + walk file (delta rows)
    df_vnb_curr,            ← CQ slice (EXPTU=1,TVOG=1,SCEN=MR)
    df_vnb_prev,            ← PQ slice (EXPTU=1,TVOG=1,SCEN=MR)
    df_vnb_curr_raw,        ← 원본 전체 (SL_TVOG 계산용)
    df_comm_curr, df_comm_prev,
    df_exp_curr
    """
    py, pq = prev_quarter(year, quarter)

    # VNB 원본
    try:
        _vnb_curr_full = pd.read_parquet(paths["vnb_curr"])
    except FileNotFoundError:
        st.error(f"당분기 VNB 없음: {paths['vnb_curr']}")
        _vnb_curr_full = pd.DataFrame()

    try:
        _vnb_prev_full = pd.read_parquet(paths["vnb_prev"])
    except FileNotFoundError:
        st.error(f"전분기 VNB 없음: {paths['vnb_prev']}")
        _vnb_prev_full = pd.DataFrame()

    # 분기 말일 계산
    curr_end = quarter_end_date(year, quarter)  # 예: 2026-03-31
    prev_end = quarter_end_date(py, pq)          # 예: 2025-12-31

    # CQ 슬라이스: 당분기 말일 + SCEN=MR, EXPTU=1, TVOG=1
    df_vnb_curr = get_vnb_cq(_vnb_curr_full, curr_end)
    # PQ 슬라이스: 전분기 말일 + SCEN=MR, EXPTU=1, TVOG=1
    df_vnb_prev = get_vnb_cq(_vnb_prev_full, prev_end)

    # Walk prefix (전분기 말일 기준으로 PQ/PQ_TVOG/PQ_ETU 추출. PQ_COMM은 df_walk_file에 이미 있음)
    prefix = _build_walk_prefix_from_df(_vnb_prev_full, py, pq)

    # CQ_TVOG step: 당분기 말일 CQ VNB 합산 (절대값, charts.py에서 delta 변환)
    cq_for_tvog = get_vnb_cq(_vnb_curr_full, curr_end)
    cq_tvog_vnb = float(cq_for_tvog["VNB"].sum()) if not cq_for_tvog.empty else 0.0
    cq_tvog_anp = float(cq_for_tvog["ANP"].sum()) if not cq_for_tvog.empty else 0.0
    cq_tvog_row = pd.DataFrame([{"STEP": "CQ_TVOG", "VNB": cq_tvog_vnb, "ANP": cq_tvog_anp}])

    # Walk file (delta rows)
    try:
        df_walk_file = pd.read_parquet(paths["vnb_walk"])
    except FileNotFoundError:
        st.error(f"Walk 없음: {paths['vnb_walk']}")
        df_walk_file = pd.DataFrame(columns=["STEP","VNB","ANP"])

    # Walk: prefix + walk steps + SL_TVOG + CQ
    # SL_TVOG와 CQ는 step_order에서 OTH_ETU 뒤에 추가
    df_vnb_walk = pd.concat([prefix, df_walk_file, cq_tvog_row], ignore_index=True)

    # MPF
    _mpf_files = paths.get("mpf_files") or _MPF_FILES
    df_mpf_curr = _load_mpf_dir(paths["mpf_curr_dir"], vnb_path=paths["vnb_curr"], mpf_files=_mpf_files)
    df_mpf_prev = _load_mpf_dir(paths["mpf_prev_dir"], vnb_path=paths["vnb_prev"], mpf_files=_mpf_files)

    # Commission (통합 commission.xlsx 우선, 없으면 원본 폴더 폴백)
    df_comm_curr, df_comm_prev = load_commission_data(paths)

    # Expense
    try:
        df_exp_curr = pd.read_csv(paths["expense_curr"])
    except FileNotFoundError:
        df_exp_curr = pd.DataFrame()

    return (df_mpf_prev, df_mpf_curr,
            df_vnb_walk, df_vnb_curr, df_vnb_prev, _vnb_curr_full, _vnb_prev_full,
            df_comm_curr, df_comm_prev, df_exp_curr)
