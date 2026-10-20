"""
utils/io/config.py — 설정(.env) 로드 및 경로 계산.

.env 파일을 읽어 나머지 코드가 기대하는 설정 dict를 만들고(load_config),
연도/분기 선택에 따른 실제 데이터 경로를 계산한다(build_paths).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 기본값 (.env / 환경변수에 값이 없을 때 사용 — 개발 편의용, 운영값은 .env에서 지정)
_DEFAULT_MPF_FILES = ["trad.parquet", "isp.parquet", "var.parquet"]


def _env_str(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _env_list(key: str, default: list[str] | None = None) -> list[str]:
    raw = os.environ.get(key, "")
    if not raw.strip():
        return list(default or [])
    return [item.strip() for item in raw.split(",") if item.strip()]


def _env_float(key: str, default: float) -> float:
    raw = os.environ.get(key)
    if raw is None or not raw.strip():
        return float(default)
    try:
        return float(raw)
    except ValueError:
        logger.warning("환경변수 %s 값(%r)이 숫자가 아니라 기본값 %s 사용", key, raw, default)
        return float(default)


@st.cache_resource
def load_config() -> dict:
    """.env 파일(프로젝트 루트)을 읽어 나머지 코드가 기대하는 설정 dict를 만든다.

    .env가 없으면 아래 기본값으로 동작한다. 기본값은 저장소에 포함된 데모 데이터
    (./demo_data, tools/make_demo_data.py로 생성한 가상 데이터)를 가리키므로
    Streamlit Community Cloud 등에서 별도 설정 없이 바로 실행된다.
    """
    load_dotenv(_PROJECT_ROOT / ".env")

    return {
        "target_info": {
            "current_q":  _env_str("NAVI_CURRENT_Q",  "2026 Q3"),
            "previous_q": _env_str("NAVI_PREVIOUS_Q", "2026 Q2"),
        },
        "paths": {
            "base_dir":    _env_str("NAVI_BASE_DIR", "./demo_data"),
            # 비워두면 base_dir/YYYY/MM/dashboard/<file_names.lob_mapping> 자동 사용
            "lob_mapping": _env_str("NAVI_LOB_MAPPING", ""),
            "file_names": {
                "vnb":              _env_str("NAVI_FILE_VNB",            "vnb.parquet"),
                "vnb_walk":         _env_str("NAVI_FILE_VNB_WALK",       "vnb-walk.parquet"),
                "commission":       _env_str("NAVI_FILE_COMMISSION",     "commission.xlsx"),
                "model_expense":    _env_str("NAVI_FILE_MODEL_EXPENSE",  "model-expense.csv"),
                "lob_mapping":      _env_str("NAVI_FILE_LOB_MAPPING",    "lob-mapping.xlsx"),
                "actual_expense":   _env_str("NAVI_FILE_ACTUAL_EXPENSE", "actual-expense.xlsx"),
                "notes":            _env_str("NAVI_FILE_NOTES",          "vnb_analysis_notes.json"),
                "fa_spread_prefix": _env_str("NAVI_FILE_FA_SPREAD_PREFIX", "fa-spread"),
                "fac_prefix":       _env_str("NAVI_FILE_FAC_PREFIX",     "VNBQ"),
                "fac_suffix":       _env_str("NAVI_FILE_FAC_SUFFIX",     "_INT_RETURN_MR.fac"),
                "mpf_files":        _env_list("NAVI_MPF_FILES", _DEFAULT_MPF_FILES),
            },
        },
        "year_options": [int(y) for y in _env_list("NAVI_YEAR_OPTIONS", ["2026"])],
        "step_order": _env_list(
            "NAVI_STEP_ORDER",
            ["MC", "RP", "SL_VOL", "SL_MIX", "SL_DEMO", "AU_COMM", "EC_NMR", "EC_FX", "SL_NEW", "OTH_COMM", "OTH_ETU"],
        ),
        "economics": {
            "plan_fx": _env_float("NAVI_PLAN_FX", 1450.0),
            "curr_fx": _env_float("NAVI_CURR_FX", 1488.0),
            "prev_fx": _env_float("NAVI_PREV_FX", 1462.0),
        },
        "analysis_settings": {
            "mix_diff_limit":    _env_float("NAVI_MIX_DIFF_LIMIT",    10.0),
            "term_others_limit": _env_float("NAVI_TERM_OTHERS_LIMIT", 1.0),
        },
    }


def _resolve_base(cfg: dict) -> Path:
    """
    base_dir를 절대경로로 변환.
    절대경로면 그대로, 상대경로면 프로젝트 루트 기준으로 resolve.
    어디서 streamlit run을 실행해도 동일하게 동작.
    """
    raw = cfg["paths"]["base_dir"]
    p = Path(raw)
    if p.is_absolute():
        return p
    return (_PROJECT_ROOT / p).resolve()


def parse_current_quarter(cfg: dict) -> tuple[int, str]:
    raw = cfg.get("target_info", {}).get("current_q", "")
    try:
        parts = raw.strip().split()
        return int(parts[0]), parts[1].upper()
    except Exception:
        return 2026, "Q1"


# ════════════════════════════════════════════════════════════════
# 분기 헬퍼
# ════════════════════════════════════════════════════════════════
_Q2M   = {"Q1": "03", "Q2": "06", "Q3": "09", "Q4": "12"}
_Q2END = {"Q1": "03-31", "Q2": "06-30", "Q3": "09-30", "Q4": "12-31"}


def quarter_to_month(q: str) -> str:
    return _Q2M[q.upper()]


def quarter_end_date(year: int, q: str) -> str:
    return f"{year}-{_Q2END[q.upper()]}"


def prev_quarter(year: int, q: str) -> tuple[int, str]:
    n = int(q[1])
    return (year - 1, "Q4") if n == 1 else (year, f"Q{n-1}")


# ════════════════════════════════════════════════════════════════
# 경로 계산
# ════════════════════════════════════════════════════════════════
def build_paths(cfg: dict, year: int, quarter: str) -> dict:
    """
    변경 사항 (v48 폴더 재구성)
    ──────────────────────────
    model-expense.csv / actual-expense.xlsx / lob-mapping.xlsx /
    trad.parquet / isp.parquet / var.parquet / commission.xlsx(통합) 는
    이제 모두 base_dir/YYYY/MM/dashboard/ 폴더 하나에 모아서 관리한다.
    (예전: analysis/, policies/, data_dir/YYYY/MM 등에 흩어져 있었음)

    commission.xlsx(통합)는 별도 배치 스크립트로 생성한 통합 파일이다.
    앱은 comm_merged_curr/prev 경로의 통합 파일만 읽으며, 파일이
    없으면 에러를 낸다(폴백 없음) — load_commission_data() 참고.
    """
    base   = _resolve_base(cfg)
    py, pq = prev_quarter(year, quarter)

    curr = base / str(year) / quarter_to_month(quarter)
    prev = base / str(py)   / quarter_to_month(pq)

    curr_dash = curr / "dashboard"
    prev_dash = prev / "dashboard"

    curr_ym = f"{year}{quarter_to_month(quarter)}"
    prev_ym = f"{py}{quarter_to_month(pq)}"

    # 파일명은 하드코딩하지 않고 .env(NAVI_FILE_*)에서 읽는다 — 폴더 구조/파일명이
    # 바뀌어도 .env만 수정하면 되고, 코드 변경이 필요 없다.
    fn = cfg.get("paths", {}).get("file_names", {})
    f_vnb          = fn.get("vnb",            "vnb.parquet")
    f_vnb_walk     = fn.get("vnb_walk",       "vnb-walk.parquet")
    f_commission   = fn.get("commission",     "commission.xlsx")
    f_model_exp    = fn.get("model_expense",  "model-expense.csv")
    f_lob_mapping  = fn.get("lob_mapping",    "lob-mapping.xlsx")
    f_actual_exp   = fn.get("actual_expense", "actual-expense.xlsx")
    f_notes        = fn.get("notes",          "vnb_analysis_notes.json")
    fa_prefix      = fn.get("fa_spread_prefix", "fa-spread")
    fac_prefix     = fn.get("fac_prefix",     "VNBQ")
    fac_suffix     = fn.get("fac_suffix",     "_INT_RETURN_MR.fac")
    mpf_files      = fn.get("mpf_files",      list(_DEFAULT_MPF_FILES))

    return {
        "vnb_curr":       str(curr / "outputs"   / f_vnb),
        "vnb_prev":       str(prev / "outputs"   / f_vnb),
        "vnb_walk":       str(curr / "outputs"   / f_vnb_walk),

        # commission 통합 결과 파일 (앱은 이것만 읽음 — 없으면 에러)
        "comm_merged_curr": str(curr_dash / f_commission),
        "comm_merged_prev": str(prev_dash / f_commission),

        # base_dir/YYYY/MM/dashboard 폴더로 통합된 파일들
        "dashboard_curr_dir": str(curr_dash),
        "dashboard_prev_dir": str(prev_dash),
        "expense_curr":   str(curr_dash / f_model_exp),
        "mpf_curr_dir":   str(curr_dash),
        "mpf_prev_dir":   str(prev_dash),
        "mpf_files":      mpf_files,
        "lob_mapping":    cfg.get("paths", {}).get("lob_mapping")    or str(curr_dash / f_lob_mapping),
        "actual_expense": str(curr_dash / f_actual_exp),
        "notes_file":     str(curr_dash / f_notes),

        "fa_spread_curr": str(curr / "scenarios" / f"{fa_prefix}-{curr_ym}.xlsx"),
        "fa_spread_prev": str(prev / "scenarios" / f"{fa_prefix}-{prev_ym}.xlsx"),
        "fac_curr": str(curr / "scenarios" / f"{fac_prefix}{quarter[1]}{fac_suffix}"),
        "fac_prev": str(prev / "scenarios" / f"{fac_prefix}{pq[1]}{fac_suffix}"),
    }
