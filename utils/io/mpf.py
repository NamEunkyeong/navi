"""
utils/io/mpf.py — MPF(trad/isp/var parquet) 로더.

mapping 없이 parquet 자체 컬럼을 사용하며, PRODUCT_GROUP1이 없는 경우
vnb.parquet 매핑으로 자동 보완한다.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import streamlit as st

from .config import _DEFAULT_MPF_FILES

# 기본값(.env의 NAVI_MPF_FILES가 없을 때 폴백) — build_paths()가 넘겨주는
# paths["mpf_files"]가 우선이며, 이 상수는 그 값이 비어있을 때만 사용된다.
_MPF_FILES = _DEFAULT_MPF_FILES


def _enrich_mpf_product_group(df_mpf: pd.DataFrame, vnb_path: str) -> pd.DataFrame:
    """MPF에 PRODUCT_GROUP1이 없을 때 vnb.parquet 매핑으로 자동 보완."""
    if "PRODUCT_GROUP1" in df_mpf.columns or df_mpf.empty:
        return df_mpf
    try:
        vnb = pd.read_parquet(vnb_path, columns=["PRODUCT", "PRODUCT_GROUP1"])
        pg_map = vnb.drop_duplicates("PRODUCT").set_index("PRODUCT")["PRODUCT_GROUP1"].to_dict()
    except Exception:
        return df_mpf
    prod_col = next(
        (c for c in ["PRODUCT", "PROD_NAME_MP", "PROD_NAME_BASE"] if c in df_mpf.columns),
        None,
    )
    if not prod_col or not pg_map:
        return df_mpf
    df_mpf = df_mpf.copy()
    df_mpf["PRODUCT_GROUP1"] = df_mpf[prod_col].map(pg_map)
    if df_mpf["PRODUCT_GROUP1"].isna().any() and "PROD_NAME_BASE" in df_mpf.columns:
        _prefix = {
            "WL_": "Whole Life", "CI_": "CI", "ANNUITY_": "Annuity",
            "ENDOW_": "Endowment", "TERM_": "Term", "UL_": "UL",
        }
        def _guess(b):
            for p, g in _prefix.items():
                if str(b).startswith(p):
                    return g
            return "Other"
        mask = df_mpf["PRODUCT_GROUP1"].isna()
        df_mpf.loc[mask, "PRODUCT_GROUP1"] = df_mpf.loc[mask, "PROD_NAME_BASE"].map(_guess)
    return df_mpf


def _load_one_mpf(fpath: str) -> pd.DataFrame | None:
    try:
        return pd.read_parquet(fpath)
    except Exception:
        return None


def _load_mpf_dir(directory: str, vnb_path: str = "", mpf_files: list[str] | None = None) -> pd.DataFrame:
    folder = Path(directory)
    if not folder.exists():
        st.warning(f"MPF 폴더 없음: {directory}")
        return pd.DataFrame()

    mpf_files = mpf_files or _MPF_FILES
    files = [folder / f for f in mpf_files if (folder / f).exists()]
    if not files:
        st.warning(f"{directory}: {'/'.join(mpf_files)} 없음")
        return pd.DataFrame()

    n_workers = min(len(files), (os.cpu_count() or 4) * 2)
    with ThreadPoolExecutor(max_workers=n_workers) as ex:
        results = list(ex.map(_load_one_mpf, [str(f) for f in files]))

    parts = [r for r in results if r is not None and not r.empty]
    if not parts:
        return pd.DataFrame()
    combined = pd.concat(parts, ignore_index=True)
    # PRODUCT_GROUP1 없으면 vnb.parquet 매핑으로 보완
    if "PRODUCT_GROUP1" not in combined.columns and vnb_path:
        combined = _enrich_mpf_product_group(combined, vnb_path)
    return combined
