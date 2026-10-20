"""
utils/io/commission.py — lob-mapping 및 통합 commission.xlsx 로더.

통합 commission.xlsx(시트: {CHANNEL}_actual /
{CHANNEL}_plan)를 읽어 채널별 plan/actual commission rate를 하나의
DataFrame으로 합친다.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════
# 통합 commission.xlsx 시트 구조
# 시트명: {CHANNEL}_actual / {CHANNEL}_plan
# 구조: C1부터 데이터 시작 (A열=PRODUCT_ITEM, B열=PRODUCT_NAME_BASE,
#       C열=보종코드, D열=납기, [E열=GA_TYPE])
#       row1/row2 이중 헤더, row3부터 데이터
# ════════════════════════════════════════════════════════════════
_MERGED_SHEET_RE = re.compile(r"^([A-Za-z]+)_(actual|plan)$", re.IGNORECASE)

_COMM_KEY_COLS = ["PRODUCT_NAME_BASE", "납기", "GA_TYPE"]


def _load_lob_map(lob_mapping_path: str) -> dict:
    """
    lob-mapping.xlsx 로드.
    PROD_NAME_BASE (예: L00001)의 앞 알파벳 제거 후 보종코드를 key로 사용.
    반환: {보종코드 → {PRODUCT, PRODUCT_GROUP1, PROD_NAME_BASE}}
    """
    if not lob_mapping_path:
        return {}
    try:
        p = Path(lob_mapping_path)
        if not p.exists():
            return {}
        lm = pd.read_excel(p, engine="openpyxl") if p.suffix in (".xlsx", ".xls") else pd.read_csv(p)
        result = {}
        prod_col = "PROD_NAME_BASE" if "PROD_NAME_BASE" in lm.columns else None
        if not prod_col:
            return {}
        for _, row in lm.iterrows():
            raw_key = str(row[prod_col]).strip()
            # L00001 → 00001 (앞 알파벳 제거)
            join_key = raw_key.lstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
            result[join_key] = {
                "PROD_NAME_BASE":  raw_key,
                "PRODUCT":         str(row.get("PRODUCT",        raw_key)),
                "PRODUCT_GROUP1":  str(row.get("PRODUCT_GROUP1", "Other")),
            }
        return result
    except Exception:
        return {}


# ════════════════════════════════════════════════════════════════
# ── 통합 commission.xlsx 로더 ────────────────────────────────────
# 시트명: {CHANNEL}_actual / {CHANNEL}_plan
# 구조: C1부터 데이터 시작 (A열=PRODUCT_ITEM, B열=PRODUCT_NAME_BASE,
#       C열=보종코드, D열=납기, [E열=GA_TYPE])
#       row1/row2 이중 헤더, row3부터 데이터
# ════════════════════════════════════════════════════════════════
_MERGED_SHEET_RE = re.compile(r"^([A-Za-z]+)_(actual|plan)$", re.IGNORECASE)

_COMM_KEY_COLS = ["PRODUCT_NAME_BASE", "납기", "GA_TYPE"]


def _explode_term(df: pd.DataFrame, col: str = "납기") -> pd.DataFrame:
    """
    '10/15', '10/15/20' 처럼 여러 납기가 한 셀에 같이 적힌 경우,
    각 납기별로 행을 나눠서(같은 값을 복제) 개별 납기로 비교할 수 있게 한다.
    이미 순수 숫자인 경우(예: '10')는 그대로 1개 행 유지.
    """
    if col not in df.columns or df.empty:
        return df
    df = df.copy()
    df[col] = df[col].astype(str).str.strip().str.split(r"\s*/\s*")
    df = df.explode(col, ignore_index=True)
    df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _dedupe_avg(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """동일 키(PRODUCT_NAME_BASE+납기+GA_TYPE) 중복 행은 평균으로 합친다."""
    if df.empty:
        return df
    key_cols = [c for c in _COMM_KEY_COLS if c in df.columns]
    if not key_cols:
        return df
    other_cols = [c for c in df.columns if c not in key_cols and c != value_col]
    agg = {value_col: "mean"}
    for c in other_cols:
        agg[c] = "first"  # PRODUCT, 보종코드 등 표시용 컬럼은 첫 값 사용
    return df.groupby(key_cols, as_index=False, dropna=False).agg(agg)


def _parse_merged_actual(raw: pd.DataFrame) -> pd.DataFrame:
    """{CHANNEL}_actual 시트 파싱. 월별(1회차+13회차) 평균 = RATE."""
    if raw.empty or raw.shape[0] < 3:
        return pd.DataFrame()

    row0 = raw.iloc[0].ffill()
    row1 = raw.iloc[1]
    data = raw.iloc[2:].reset_index(drop=True)

    key_map: dict = {}
    month_cols: dict = {}
    months: list = []

    for ci in range(2, len(row1)):  # ci=0,1은 PRODUCT_ITEM/PRODUCT_NAME_BASE, 건너뜀
        top = str(row0.iloc[ci]).strip()
        sub = str(row1.iloc[ci]).strip()
        sub_norm = sub.upper().replace(" ", "_")

        if sub == "보종코드":
            key_map["보종코드"] = ci
        elif sub == "납기":
            key_map["납기"] = ci
        elif sub_norm == "GA_TYPE":
            key_map["GA_TYPE"] = ci
        elif sub == "보종명":
            continue
        elif sub == "1회차":
            skip_top = top in ("", "NAN", "보종코드", "납기", "보종명") or top.upper().replace(" ", "_") == "GA_TYPE"
            if not skip_top:
                if top not in month_cols:
                    month_cols[top] = []
                    months.append(top)
                month_cols[top].append(ci)
        elif sub == "13회차" and months:
            month_cols[months[-1]].append(ci)

    df = pd.DataFrame()
    df["PRODUCT_ITEM"]       = data.iloc[:, 0].astype(str).str.strip()
    df["PRODUCT_NAME_BASE"]  = data.iloc[:, 1].astype(str).str.strip()
    if "보종코드" in key_map:
        df["보종코드"] = data.iloc[:, key_map["보종코드"]].astype(str).str.strip().str.zfill(5)
    if "납기" in key_map:
        df["납기"] = data.iloc[:, key_map["납기"]].astype(str).str.strip()
    df["GA_TYPE"] = (data.iloc[:, key_map["GA_TYPE"]].astype(str).str.strip()
                     if "GA_TYPE" in key_map else "All")

    totals = []
    for mm in months:
        v = pd.Series(0.0, index=data.index)
        for ci in month_cols.get(mm, []):
            v = v + pd.to_numeric(data.iloc[:, ci], errors="coerce").fillna(0)
        totals.append(v)
    df["RATE"] = sum(totals) / len(totals) if totals else 0.0

    if "보종코드" in df.columns:
        df = df.dropna(subset=["보종코드"])
        df = df[df["보종코드"].str.match(r"^\d+$")]
    df = df.reset_index(drop=True)
    df = _explode_term(df, "납기")
    return _dedupe_avg(df, "RATE")


def _parse_merged_plan(raw: pd.DataFrame) -> pd.DataFrame:
    """{CHANNEL}_plan 시트 파싱. 1회차+13회차 합산 = PLAN."""
    if raw.empty or raw.shape[0] < 3:
        return pd.DataFrame()

    row1 = raw.iloc[1]
    data = raw.iloc[2:].reset_index(drop=True)

    col_map: dict = {}
    for ci in range(2, len(row1)):  # ci=0,1은 PRODUCT_ITEM/PRODUCT_NAME_BASE, 건너뜀
        lab = str(row1.iloc[ci]).strip()
        lab_norm = lab.upper().replace(" ", "_")
        if lab == "보종코드":
            col_map["보종코드"] = ci
        elif lab == "납기":
            col_map["납기"] = ci
        elif lab_norm == "GA_TYPE":
            col_map["GA_TYPE"] = ci
        elif lab == "1회차":
            col_map["1회차"] = ci
        elif lab == "13회차":
            col_map["13회차"] = ci

    result = pd.DataFrame()
    result["PRODUCT_ITEM"]      = data.iloc[:, 0].astype(str).str.strip()
    result["PRODUCT_NAME_BASE"] = data.iloc[:, 1].astype(str).str.strip()
    if "보종코드" in col_map:
        result["보종코드"] = data.iloc[:, col_map["보종코드"]].astype(str).str.strip().str.zfill(5)
    if "납기" in col_map:
        result["납기"] = data.iloc[:, col_map["납기"]].astype(str).str.strip()
    result["GA_TYPE"] = (data.iloc[:, col_map["GA_TYPE"]].astype(str).str.strip()
                         if "GA_TYPE" in col_map else "All")

    v = pd.Series(0.0, index=data.index)
    if "1회차" in col_map:  v = v + pd.to_numeric(data.iloc[:, col_map["1회차"]],  errors="coerce").fillna(0)
    if "13회차" in col_map: v = v + pd.to_numeric(data.iloc[:, col_map["13회차"]], errors="coerce").fillna(0)
    result["PLAN"] = v

    if "보종코드" in result.columns:
        result = result.dropna(subset=["보종코드"])
        result = result[result["보종코드"].str.match(r"^\d+$")]
    result = result.reset_index(drop=True)
    result = _explode_term(result, "납기")
    return _dedupe_avg(result, "PLAN")


def load_commission_merged(path: str, lob_mapping_path: str = "") -> pd.DataFrame:
    """
    통합 commission.xlsx 로드.

    plan/actual/prev 비교 시 보종코드는 분기마다 바뀔 수 있으므로,
    PRODUCT_NAME_BASE + 납기 + GA_TYPE 기준으로 actual/plan을 매칭한다.
    (보종코드는 참고용으로만 함께 보존. 동일 키로 중복된 행은 평균으로 합쳐짐)

    반환 컬럼: PRODUCT_ITEM, PRODUCT_NAME_BASE, PRODUCT, 보종코드, 납기, GA_TYPE,
              CHANNEL, RATE, PLAN, PRODUCT_GROUP1(있으면)
    """
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    try:
        xl = pd.ExcelFile(p, engine="openpyxl")
    except Exception as e:
        logger.warning(f"통합 commission 파일 읽기 실패: {path} — {e}")
        return pd.DataFrame()

    lob_map = _load_lob_map(lob_mapping_path)  # PRODUCT_GROUP1 보완용 (동일 분기 내 매칭이라 안전)

    sheets_by_channel: dict = {}
    for sheet in xl.sheet_names:
        m = _MERGED_SHEET_RE.match(sheet)
        if not m:
            continue
        channel, tag = m.group(1).upper(), m.group(2).lower()
        sheets_by_channel.setdefault(channel, {})[tag] = sheet

    parts = []
    for channel, tags in sheets_by_channel.items():
        df_actual = pd.DataFrame()
        df_plan   = pd.DataFrame()
        if "actual" in tags:
            df_actual = _parse_merged_actual(xl.parse(tags["actual"], header=None))
        if "plan" in tags:
            df_plan = _parse_merged_plan(xl.parse(tags["plan"], header=None))

        key_cols = [c for c in ["PRODUCT_NAME_BASE", "납기", "GA_TYPE"]
                    if c in df_actual.columns and c in df_plan.columns]

        if not df_actual.empty and not df_plan.empty and key_cols:
            df_merged = pd.merge(
                df_actual, df_plan[key_cols + ["PLAN"]], on=key_cols, how="left"
            )
            df_merged["PLAN"] = df_merged["PLAN"].fillna(0.0)
        elif not df_actual.empty:
            df_merged = df_actual.copy()
            df_merged["PLAN"] = 0.0
        elif not df_plan.empty:
            df_merged = df_plan.copy()
            df_merged["RATE"] = 0.0
        else:
            continue

        df_merged["CHANNEL"] = channel
        df_merged["PRODUCT"] = df_merged["PRODUCT_NAME_BASE"]

        if lob_map and "보종코드" in df_merged.columns:
            df_merged["PRODUCT_GROUP1"] = df_merged["보종코드"].map(
                lambda x: lob_map.get(str(x).strip(), {}).get("PRODUCT_GROUP1", "Other"))

        parts.append(df_merged)

    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def load_commission_data(paths: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Commission 로드 진입점.
    통합 commission.xlsx(comm_merged_curr/prev)만 읽는다. (원본 폴더 폴백 없음)
    """
    lob_path         = paths.get("lob_mapping", "")
    merged_curr_path = paths.get("comm_merged_curr", "")
    merged_prev_path = paths.get("comm_merged_prev", "")

    if not merged_curr_path or not Path(merged_curr_path).exists():
        raise FileNotFoundError(
            f"통합 commission 파일이 없습니다: {merged_curr_path}\n"
            f"→ 데모 데이터는 `python tools/make_demo_data.py` 로 생성합니다."
        )
    if not merged_prev_path or not Path(merged_prev_path).exists():
        raise FileNotFoundError(
            f"통합 commission 파일이 없습니다: {merged_prev_path}\n"
            f"→ 데모 데이터는 `python tools/make_demo_data.py` 로 생성합니다."
        )

    df_comm_curr = load_commission_merged(merged_curr_path, lob_path)
    df_comm_prev = load_commission_merged(merged_prev_path, lob_path)
    return df_comm_curr, df_comm_prev
