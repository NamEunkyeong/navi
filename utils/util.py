import pandas as pd
"""
utils/util.py
─────────────
통화 변환 및 값 포맷팅 유틸리티.
"""

# 백만 단위 변환 상수 (모든 모듈에서 공유)
MILLION = 1_000_000


def convert_currency(df, target_curr: str, rate: float, is_mpf: bool = False, fx_krw: float = 1.0):
    """
    데이터프레임의 금액 컬럼을 target_curr 기준으로 환산한다.
    is_mpf=True일 때: CURRENCY==USD인 행의 SUM_ASSURED, ANNUAL_PREM_P2, ANP에 fx_krw를 먼저 곱함.
    원본을 훼손하지 않도록 복사본을 반환한다.
    """
    df_conv = df.copy()

    # MPF USD 계약에 FX 적용 (원화 환산)
    if is_mpf and fx_krw and fx_krw != 1.0 and "CURRENCY" in df_conv.columns:
        mpf_fx_cols = [c for c in ["SUM_ASSURED", "ANNUAL_PREM_P2", "ANP"] if c in df_conv.columns]
        usd_mask = df_conv["CURRENCY"] == "USD"
        for col in mpf_fx_cols:
            df_conv.loc[usd_mask, col] = df_conv.loc[usd_mask, col] * fx_krw

    # display currency 변환 (KRW→USD)
    amount_cols = ["ANP", "VNB", "CD", "SUM_ASSURED", "ANNUAL_PREM_P2"]
    if target_curr == "USD":
        for col in amount_cols:
            if col in df_conv.columns:
                df_conv[col] /= rate
    return df_conv


def format_value(val, fmt_type: str = "amount") -> str:
    """
    표 셀 값을 타입에 맞게 포맷팅한다.  단위: Millions.

    fmt_type
    ────────
    amount       : 금액 (백만 단위, 소수점 1자리)          예) 1,234.5
    percent      : 비율 (소수점 2자리 + %)                 예) 12.34%
    diff_amount  : 금액 차이 (부호 포함, 백만 단위)         예) +1.5 / -2.0
    diff_percent : 비율 차이 (부호 포함, %p)               예) +0.12%p
    """
    try:
        if not isinstance(val, (int, float)):
            return val
        if fmt_type == "amount":
            return f"{val / MILLION:,.1f}"
        if fmt_type == "percent":
            return f"{val:.2f}%"
        if fmt_type == "diff_amount":
            return f"{val / MILLION:+,.1f}"
        if fmt_type == "diff_percent":
            return f"{val:+.2f}%p"
        return str(val)
    except Exception:
        return val

def safe_fillna(df: "pd.DataFrame", value=0) -> "pd.DataFrame":
    """Categorical 컬럼을 object로 변환 후 fillna 적용."""
    for col in df.columns:
        if hasattr(df[col], "cat"):
            df[col] = df[col].astype(object)
    return df.fillna(value).infer_objects(copy=False)

