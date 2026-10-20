"""
utils/processor.py
──────────────────
데이터 집계·변환 함수 모음.

컬럼 규칙
─────────
MPF: PREM_PERIOD(납기), AGE(가입나이), DEFER_Y(거치기간), ANP
VNB: PRODUCT_GROUP1(필터), PRODUCT_GROUP2(Summary 추가), CURRENCY(Summary 추가)
     PRODUCT(Sales Mix 포트폴리오), PRODUCT_ITEM(Demo Detailed Mix)
"""
import pandas as pd
from pathlib import Path


# ── 공통 필터 ─────────────────────────────────────────────────────


def filter_data(
    df: pd.DataFrame,
    target_pg: str,
    target_ch: str,
    target_ct: str = "All",
    target_prod: str = "All",
) -> pd.DataFrame:
    """
    PRODUCT_GROUP1 / CHANNEL / CONTRACT_TYPE / PRODUCT 필터.
    Walk DataFrame의 경우: 고정 step (PQ/CQ 등)도 필터 적용하여 값 변경.
    Non-walk DataFrame의 경우: 모두 필터 적용.
    """
    tmp = df.copy()

    if target_pg != "Company Total" and "PRODUCT_GROUP1" in tmp.columns:
        tmp = tmp[tmp["PRODUCT_GROUP1"] == target_pg]
    if target_ch != "Company Total" and "CHANNEL" in tmp.columns:
        tmp = tmp[tmp["CHANNEL"] == target_ch]
    if target_ct != "All" and "CONTRACT_TYPE" in tmp.columns:
        tmp = tmp[tmp["CONTRACT_TYPE"] == target_ct]
    if target_prod != "All" and "PRODUCT" in tmp.columns:
        tmp = tmp[tmp["PRODUCT"] == target_prod]

    return tmp.copy()


# ── Mix 집계 ──────────────────────────────────────────────────────
def get_dim_mix(df: pd.DataFrame, dim: str) -> pd.DataFrame:
    """dim 차원의 ANP 비중(Mix %)."""
    if df.empty or dim not in df.columns:
        return pd.DataFrame(columns=[dim, "ANP", "Mix(%)"])
    mix   = df.groupby(dim)["ANP"].sum().reset_index()
    total = mix["ANP"].sum()
    mix["Mix(%)"] = (mix["ANP"] / total * 100).fillna(0) if total > 0 else 0.0
    return mix


def get_contract_type_mix(df_p: pd.DataFrame, df_c: pd.DataFrame) -> pd.DataFrame:
    """CONTRACT_TYPE별 ANP Mix(%) 전분기 vs 당분기."""
    if "CONTRACT_TYPE" not in df_c.columns:
        return pd.DataFrame()
    mix_p = get_dim_mix(df_p, "CONTRACT_TYPE").rename(columns={"Mix(%)": "Prev. Mix(%)", "ANP": "Prev. ANP"})
    mix_c = get_dim_mix(df_c, "CONTRACT_TYPE").rename(columns={"Mix(%)": "Curr. Mix(%)", "ANP": "Curr. ANP"})
    ct    = pd.merge(mix_p, mix_c, on="CONTRACT_TYPE", how="outer")
    for _c in ct.columns:
        if hasattr(ct[_c], "cat"):
            ct[_c] = ct[_c].astype(object)
    ct = ct.fillna(0)
    ct["Diff(%p)"] = ct["Curr. Mix(%)"] - ct["Prev. Mix(%)"]
    return ct


# ── 납기 분포 (PREM_PERIOD) ──────────────────────────────────────
def get_term_mix(df: pd.DataFrame, other_limit: float = 1.0) -> pd.DataFrame:
    """PREM_PERIOD 기준 ANP 비중. other_limit 이하는 Others로 묶음."""
    col = "PREM_PERIOD"
    if df.empty or col not in df.columns:
        return pd.DataFrame(columns=[col, "Mix(%)"])

    tm    = df.groupby(col)["ANP"].sum().reset_index()
    total = tm["ANP"].sum()
    tm["Mix(%)"] = (tm["ANP"] / total * 100).fillna(0) if total > 0 else 0.0

    main       = tm[tm["Mix(%)"] > other_limit][[col, "Mix(%)"]].copy()
    main[col]  = main[col].astype(str)
    others_val = tm[tm["Mix(%)"] <= other_limit]["Mix(%)"].sum()
    if others_val > 0:
        main = pd.concat([main, pd.DataFrame({col: ["Others"], "Mix(%)": [others_val]})],
                         ignore_index=True)
    return main


# ── 연령 분포 (AGE) ───────────────────────────────────────────────
def get_age_group_mix(df: pd.DataFrame) -> pd.DataFrame:
    """AGE 기준 연령대별 ANP 비중."""
    col = "AGE"
    if df.empty or col not in df.columns:
        return pd.DataFrame(columns=["Age Group", "Mix(%)"])

    tmp    = df.copy()
    bins   = [0, 29, 39, 49, 59, 69, 150]
    labels = ["Under 30", "30s", "40s", "50s", "60s", "Over 70"]
    tmp["Age Group"] = pd.cut(tmp[col], bins=bins, labels=labels, right=True)

    ag    = tmp.groupby("Age Group", observed=True)["ANP"].sum().reset_index()
    total = ag["ANP"].sum()
    ag["Mix(%)"] = (ag["ANP"] / total * 100).fillna(0) if total > 0 else 0.0
    return ag


# ── 거치기간 분포 (DEFER_Y) ──────────────────────────────────
# ── 거치기간 평균 (DEFER_Y, 0 초과 계약만) ──────────────────
def get_defer_avg(df: pd.DataFrame) -> float | None:
    """
    DEFER_Y > 0인 계약만 대상으로 ANP 가중 평균 거치기간을 반환한다.
    거치기간이 있는 계약이 없으면 None을 반환한다.
    """
    col = "DEFER_Y"
    if df.empty or col not in df.columns or "ANP" not in df.columns:
        return None
    sub = df[df[col] > 0].copy()
    if sub.empty or sub["ANP"].sum() <= 0:
        return None
    return float((sub[col] * sub["ANP"]).sum() / sub["ANP"].sum())


def get_defer_mix(df: pd.DataFrame, other_limit: float = 1.0) -> pd.DataFrame:
    """
    DEFER_Y 기준 ANP 비중.
    DEFER_Y = 연금개시나이 - 가입나이 (거치 기간, 연 단위).
    0이면 즉시연금 또는 비연금.
    """
    col = "DEFER_Y"
    if df.empty or col not in df.columns:
        return pd.DataFrame(columns=[col, "Mix(%)"])

    dm    = df.groupby(col)["ANP"].sum().reset_index()
    total = dm["ANP"].sum()
    dm["Mix(%)"] = (dm["ANP"] / total * 100).fillna(0) if total > 0 else 0.0

    main       = dm[dm["Mix(%)"] > other_limit][[col, "Mix(%)"]].copy()
    main[col]  = main[col].astype(str)
    others_val = dm[dm["Mix(%)"] <= other_limit]["Mix(%)"].sum()
    if others_val > 0:
        main = pd.concat([main, pd.DataFrame({col: ["Others"], "Mix(%)": [others_val]})],
                         ignore_index=True)
    return main


# ── Ticket Size (PRODUCT 기준) ────────────────────────────────────
def calc_ticket_size_v2(df: pd.DataFrame) -> pd.DataFrame:
    """
    상품별 평균 Ticket Size (ANP / CNT).
    PRODUCT → PROD_NAME_MP → PROD_NAME_BASE 순으로 폴백.
    """
    if df.empty:
        return pd.DataFrame(columns=["PRODUCT", "Ticket Size"])
    prod_col = next(
        (c for c in ["PRODUCT", "PROD_NAME_MP", "PROD_NAME_BASE"] if c in df.columns),
        None
    )
    if prod_col is None:
        return pd.DataFrame(columns=["PRODUCT", "Ticket Size"])
    tmp = df.copy()
    if "CNT" not in tmp.columns:
        tmp["CNT"] = 1
    agg = tmp.groupby(prod_col).agg({"ANP": "sum", "CNT": "sum"})
    agg["Ticket Size"] = (agg["ANP"] / agg["CNT"]).fillna(0)
    result = agg[["Ticket Size"]].reset_index()
    result = result.rename(columns={prod_col: "PRODUCT"})
    return result


# ── Commission ────────────────────────────────────────────────────
def get_comm_data(
    df_comm_curr: pd.DataFrame,
    df_comm_prev: pd.DataFrame,
    lob_mapping_path: str = "",
) -> pd.DataFrame:
    """
    load_commission_data() 결과를 받아 CQ/PQ/PLAN 비교표 생성.

    df_comm_curr: PRODUCT, PRODUCT_ITEM, PRODUCT_NAME_BASE, 납기, GA_TYPE, CHANNEL, RATE, PLAN
    df_comm_prev: 동일 구조 (RATE = PQ 실적)

    분기마다 보종코드(PLICD)가 바뀔 수 있어 PLICD는 매칭 키로 쓰지 않는다.
    대신 PRODUCT_NAME_BASE(상품 기준 식별자) + 납기 + GA_TYPE 으로 매칭한다.
    (통합 commission.xlsx가 없어 구버전 로더로 폴백된 경우에는 PRODUCT/PLICD로 매칭)

    표시용 PRODUCT 컬럼에는 PRODUCT_ITEM 값을 사용한다 (없으면 PRODUCT_NAME_BASE로 대체).

    반환: PRODUCT, CHANNEL, 납기, PLAN(%), PQ(%), CQ(%), CQ-PQ, CQ-PLAN
    """
    if df_comm_curr.empty:
        return pd.DataFrame()

    if "PRODUCT_NAME_BASE" in df_comm_curr.columns:
        KEY_CANDIDATES = ["PRODUCT_NAME_BASE", "CHANNEL", "납기", "GA_TYPE"]
    else:
        KEY_CANDIDATES = ["PRODUCT", "PLICD", "CHANNEL", "납기", "GA_TYPE"]
    key_cols = [c for c in KEY_CANDIDATES if c in df_comm_curr.columns]

    # PRODUCT_ITEM은 매칭 키가 아니라 표시용으로만 같이 들고 감
    display_extra = [c for c in ["PRODUCT_ITEM"] if c in df_comm_curr.columns]

    df_cq = df_comm_curr[key_cols + display_extra +
                          [c for c in ["RATE","PLAN"] if c in df_comm_curr.columns]].copy()
    df_cq = df_cq.rename(columns={"RATE": "CQ"})

    if not df_comm_prev.empty and "RATE" in df_comm_prev.columns:
        pq_key = [c for c in key_cols if c in df_comm_prev.columns]
        df_pq  = df_comm_prev[pq_key + ["RATE"]].rename(columns={"RATE": "PQ"})
        df     = pd.merge(df_cq, df_pq, on=pq_key, how="left")
    else:
        df = df_cq.copy()
        df["PQ"] = 0.0

    # 숫자 컬럼만 0으로 채움 (PRODUCT_ITEM 등 문자열 컬럼이 0으로 깨지는 것 방지)
    num_cols = [c for c in ["CQ", "PQ", "PLAN"] if c in df.columns]
    df[num_cols] = df[num_cols].fillna(0)

    for raw, pct in [("CQ","CQ(%)"), ("PQ","PQ(%)"), ("PLAN","PLAN(%)")]:
        if raw in df.columns:
            df[pct] = (df[raw] * 100).round(4)

    df["CQ-PQ"]   = (df.get("CQ(%)",   pd.Series(0, index=df.index)) -
                     df.get("PQ(%)",   pd.Series(0, index=df.index))).round(4)
    df["CQ-PLAN"] = (df.get("CQ(%)",   pd.Series(0, index=df.index)) -
                     df.get("PLAN(%)", pd.Series(0, index=df.index))).round(4)

    # 표시용 PRODUCT 컬럼 보정: PRODUCT_ITEM 우선, 없으면 PRODUCT_NAME_BASE
    # (actual/CQ 기준 left merge라 PRODUCT_ITEM은 항상 curr에서 채워지지만,
    #  혹시 비어있는 경우를 대비해 PRODUCT_NAME_BASE로 대체)
    if "PRODUCT_ITEM" in df.columns:
        df["PRODUCT"] = df["PRODUCT_ITEM"]
        if "PRODUCT_NAME_BASE" in df.columns:
            df["PRODUCT"] = df["PRODUCT"].fillna(df["PRODUCT_NAME_BASE"])
            blank = df["PRODUCT"].astype(str).str.strip().eq("")
            df.loc[blank, "PRODUCT"] = df.loc[blank, "PRODUCT_NAME_BASE"]
    elif "PRODUCT_NAME_BASE" in df.columns:
        df["PRODUCT"] = df["PRODUCT_NAME_BASE"]

    prod_col = "PRODUCT" if "PRODUCT" in df.columns else ("PRODUCT_NAME_BASE" if "PRODUCT_NAME_BASE" in df.columns else "PLICD")
    extra    = [c for c in ["납기", "GA_TYPE"] if c in df.columns]
    ret_cols = [prod_col, "CHANNEL"] + extra + ["PLAN(%)", "PQ(%)", "CQ(%)", "CQ-PQ", "CQ-PLAN"]
    return df[[c for c in ret_cols if c in df.columns]]

# ── Expense (expense.csv 기반) ───────────────────────────────────
_VAR_MAP = {
    "ANP":  "EEV_ACQ_EXP_ANP_IF",
    "SC":   "EEV_ACQ_EXP_FYC_IF",
    "PNI":  "EEV_ACQ_EXP_POL_IF",
    "COMM": "EEV_TOT_COMM",
}


def load_actual_expense(fpath: str, channel: str = "Company Total") -> dict:
    """
    actual-expense.xlsx에서 CHANNEL, DRIVER별 EXPENSE를 읽어
    {ANP: float, SC: float, PNI: float, COMM: float} dict 반환.
    channel이 없으면 "Company Total" 사용.
    """
    p = Path(fpath)
    if not p.exists():
        return {}
    try:
        df = pd.read_excel(p, engine="openpyxl")
        df.columns = [c.strip() for c in df.columns]
        # channel 필터
        ch_key = channel if channel in df["CHANNEL"].values else "Company Total"
        df_ch  = df[df["CHANNEL"] == ch_key]
        return dict(zip(df_ch["DRIVER"], df_ch["EXPENSE"].astype(float)))
    except Exception:
        return {}


def get_expense_data(
    df_curr: pd.DataFrame,
    df_prev: pd.DataFrame = None,
    channel: str = "Company Total",
    actual_curr: dict | None = None,
) -> pd.DataFrame:
    """
    expense.csv(Model)와 actual_curr(실제 비용)을 비교하는 표를 반환한다.
    Prev 비교는 없음 — Actual vs Model만 표시.

    VAR 매핑 (Model)
    ─────────
    ANP  ← EEV_ACQ_EXP_ANP_IF
    SC   ← EEV_ACQ_EXP_FYC_IF
    PNI  ← EEV_ACQ_EXP_POL_IF
    COMM ← EEV_TOT_COMM
    """
    # df_curr가 비어있어도 컬럼 구조는 유지
    row_order_default = ["ANP", "SC", "PNI", "ACQ_TOTAL", "COMM", "TOTAL"]
    if df_curr is None or df_curr.empty:
        _empty = pd.DataFrame({
            "Actual":        [0.0] * len(row_order_default),
            "Model":         [0.0] * len(row_order_default),
            "Actual / Model":[0.0] * len(row_order_default),
            "Actual - Model":[0.0] * len(row_order_default),
            "AFT_TAX":       [0.0] * len(row_order_default),
        }, index=row_order_default)
        return _empty

    def _sum_var(df: pd.DataFrame, var_code: str, ch: str) -> float:
        if df.empty or "VAR" not in df.columns:
            return 0.0
        mask = df["VAR"] == var_code
        if ch != "Company Total" and "CHANNEL" in df.columns:
            mask = mask & (df["CHANNEL"] == ch)
        sub = df.loc[mask]
        if sub.empty:
            return 0.0
        # "sum" 컬럼이 있으면 그대로, 없으면 숫자 컬럼 합산
        if "sum" in sub.columns:
            return float(sub["sum"].sum())
        num_cols = [c for c in sub.columns
                    if c not in ("LOB","NB_M","CHANNEL","VAR")
                    and pd.api.types.is_numeric_dtype(sub[c])]
        return float(sub[num_cols].values.sum()) if num_cols else 0.0

    MILLION = 1_000_000

    rows_model = {}
    for label, var_code in _VAR_MAP.items():
        rows_model[label] = _sum_var(df_curr, var_code, channel)

    # 소계 / 합계
    rows_model["ACQ_TOTAL"] = rows_model["ANP"] + rows_model["SC"] + rows_model["PNI"]
    rows_model["TOTAL"]     = rows_model["ACQ_TOTAL"] + rows_model["COMM"]

    row_order = ["ANP", "SC", "PNI", "ACQ_TOTAL", "COMM", "TOTAL"]
    # Model: CSV 원단위 → 백만 단위로 변환해서 저장
    df = pd.DataFrame({
        "Model": [rows_model[r] / MILLION for r in row_order],
    }, index=row_order)

    # Actual 값 (yaml 원단위 입력 → 백만 단위로 변환)
    if actual_curr:
        act = dict(actual_curr)
        act["ACQ_TOTAL"] = act.get("ANP",0) + act.get("SC",0) + act.get("PNI",0)
        act["TOTAL"]     = act["ACQ_TOTAL"] + act.get("COMM",0)
        df["Actual"] = [act.get(r, 0) / MILLION for r in row_order]
    else:
        df["Actual"] = df["Model"]  # fallback

    df["Actual / Model"] = (df["Actual"] / df["Model"])                             .replace([float("inf"), float("-inf")], 0).fillna(0)
    df["Actual - Model"] = df["Actual"] - df["Model"]
    df["AFT_TAX"]        = df["Actual - Model"] * (1 - 0.28136)
    # 컬럼 순서: Actual, Model, Actual/Model, Actual-Model, AFT_TAX  (단위: 백만원)
    return df[["Actual", "Model", "Actual / Model", "Actual - Model", "AFT_TAX"]]


# ════════════════════════════════════════════════════════════════
# FA Spread 로더
# ════════════════════════════════════════════════════════════════
def load_fa_spread(fpath: str) -> pd.DataFrame:
    """
    fa-spread-YYYYMM.xlsx의 Summary 시트에서 SPREAD 영역을 읽어
    PRODUCT, SPREAD 컬럼의 DataFrame으로 반환.
    파일 없으면 빈 DataFrame 반환.
    """
    p = Path(fpath)
    if not p.exists():
        return pd.DataFrame(columns=["PRODUCT", "SPREAD"])
    try:
        wb  = pd.ExcelFile(fpath, engine="openpyxl")
        if "Summary" not in wb.sheet_names:
            return pd.DataFrame(columns=["PRODUCT", "SPREAD"])
        df = wb.parse("Summary")
        # SPREAD 영역: PRODUCT, SPREAD 컬럼 추출
        if "PRODUCT" in df.columns and "SPREAD" in df.columns:
            return df[["PRODUCT", "SPREAD"]].dropna(subset=["PRODUCT"]).reset_index(drop=True)
        # 이름이 다를 경우 첫 두 컬럼 사용
        df.columns = df.columns.astype(str).str.strip()
        spread_cols = [c for c in df.columns if "SPREAD" in c.upper()]
        prod_cols   = [c for c in df.columns if "PRODUCT" in c.upper() or "PROD" in c.upper()]
        if prod_cols and spread_cols:
            out = df[[prod_cols[0], spread_cols[0]]].copy()
            out.columns = ["PRODUCT", "SPREAD"]
            return out.dropna(subset=["PRODUCT"]).reset_index(drop=True)
        return pd.DataFrame(columns=["PRODUCT", "SPREAD"])
    except Exception:
        return pd.DataFrame(columns=["PRODUCT", "SPREAD"])

