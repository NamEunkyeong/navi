"""
dashboard.py
────────────
VNB Walk Analysis 메인 대시보드 (Pro Edition).

실행:
    streamlit run dashboard.py

구조:
    dashboard.py          ── 페이지 설정 · 사이드바 · 데이터 로드 · 탭 디스패치
    i18n.py               ── Korean / English 화면 문구
    html_export.py        ── 오프라인 HTML 보고서 생성
    tabs/summary.py       ── Summary 탭
    tabs/sales_mix.py     ── Sales Mix 탭
    tabs/demo.py          ── Demo 탭
    tabs/economic.py      ── Economic 탭
    tabs/commission.py    ── Commission 탭
    tabs/expense.py       ── Expense 탭
"""

from types import SimpleNamespace

import pandas as pd
import streamlit as st

# ── 다국어 및 HTML Export ─────────────────────────────────────
from html_export import HtmlReport
from i18n import get_translator

# ── 내부 모듈 ─────────────────────────────────────────────────
from styles.theme import C_DEEP_BLUE
from styles.utils import local_css

from utils.io import (
    _paths_mtime,
    build_filtered_walk,
    build_paths,
    get_vnb_cq,
    load_all_data,
    load_config,
    parse_current_quarter,
    prev_quarter,
    quarter_end_date,
)
from utils.util import convert_currency, format_value
from utils.components import render_top_header, render_footer

from tabs import summary as tab_summary
from tabs import sales_mix as tab_sales_mix
from tabs import demo as tab_demo
from tabs import economic as tab_economic
from tabs import commission as tab_commission
from tabs import expense as tab_expense


@st.cache_data(show_spinner=False)
def _cached_filtered_walk(
    _df_prev_full,
    _df_curr_full,
    _df_walk,
    year,
    quarter,
    channel,
    product_group,
    fx_rate,
    display_currency,
    product="All",
):
    """필터된 walk를 캐시해서 필터 변경 시 전체 재계산을 방지한다."""
    return build_filtered_walk(
        _df_prev_full,
        _df_curr_full,
        _df_walk,
        year,
        quarter,
        channel=channel,
        product_group=product_group,
        product=product,
        fx_rate=fx_rate,
        display_currency=display_currency,
    )


# ════════════════════════════════════════════════════════════════
# 1. 설정 로드
# ════════════════════════════════════════════════════════════════
cfg = load_config()

CURR_FX_RATE = cfg["economics"]["curr_fx"]
PREV_FX_RATE = cfg["economics"]["prev_fx"]
PLAN_FX_RATE = cfg["economics"]["plan_fx"]

OTHER_LIMIT = cfg["analysis_settings"]["term_others_limit"]

_WALK_STEPS = cfg.get("step_order", [])

PQ_PREFIX = [
    "PQ",
    "PQ_TVOG",
    "PQ_ETU",
    "PQ_COMM",
]

STEP_ORDER = (
    PQ_PREFIX
    + _WALK_STEPS
    + ["CQ_TVOG", "CQ"]
)

DEFAULT_YEAR, DEFAULT_QUARTER = parse_current_quarter(cfg)


# ════════════════════════════════════════════════════════════════
# 2. 페이지 설정
# ════════════════════════════════════════════════════════════════
st.set_page_config(
    layout="wide",
    page_title="VNB Walk Analysis",
    page_icon="📊",
    initial_sidebar_state="expanded",
)

local_css("styles/style.css")


# 사이드바 버튼 색상
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] button[kind="secondary"],
    section[data-testid="stSidebar"] div.stButton button {
        background-color: #003652 !important;
        background: #003652 !important;
        color: #CBF1FF !important;
        border: 1px solid rgba(200, 230, 255, 0.4) !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] button[kind="secondary"]:hover,
    section[data-testid="stSidebar"] div.stButton button:hover {
        background-color: #154865 !important;
        background: #154865 !important;
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# 접이식 섹션 제목 스타일
st.markdown(
    f"""
    <style>
    div[data-testid="stExpander"] summary {{
        font-size: 1.15rem !important;
    }}

    div[data-testid="stExpander"] summary p {{
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: {C_DEEP_BLUE} !important;
    }}

    .streamlit-expanderHeader {{
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: {C_DEEP_BLUE} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ════════════════════════════════════════════════════════════════
# 3. Global Setting
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-logo">
            <h2>📊 VNB Analytics</h2>
            <p>Value of New Business Walk</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Language 위젯을 표시하기 전에는 아직 번역 함수를 만들 수 없으므로
    # Global Setting과 Display Currency는 공통 영문 라벨을 사용한다.
    st.header("Global Setting")

    display_currency = st.radio(
        "Display Currency",
        ["KRW", "USD"],
        help=(
            "전체 데이터를 선택한 통화로 환산하여 표시합니다. "
            "All monetary values are displayed in the selected currency."
        ),
    )

    language = st.radio(
        "Language",
        ["Korean", "English"],
        horizontal=True,
        help=(
            "대시보드 화면과 분석 보고서의 표시 언어를 선택합니다. "
            "Select the display language for the dashboard "
            "and analysis reports."
        ),
    )

    t = get_translator(language)

    st.header(t("time_selection"))

    _year_options = cfg.get(
        "year_options",
        [DEFAULT_YEAR],
    )

    _year_idx = (
        _year_options.index(DEFAULT_YEAR)
        if DEFAULT_YEAR in _year_options
        else len(_year_options) - 1
    )

    _qtr_options = [
        "Q1",
        "Q2",
        "Q3",
        "Q4",
    ]

    _qtr_idx = (
        _qtr_options.index(DEFAULT_QUARTER)
        if DEFAULT_QUARTER in _qtr_options
        else 0
    )

    year = st.selectbox(
        t("year"),
        _year_options,
        index=_year_idx,
    )

    quarter = st.selectbox(
        t("quarter"),
        _qtr_options,
        index=_qtr_idx,
    )

    st.header(t("fx_rate"))

    fx_rate = st.number_input(
        t("fx_rate_input"),
        value=float(PLAN_FX_RATE),
        min_value=1.0,
        step=1.0,
        format="%.1f",
    )

    # Display Options는 제거한다.
    # 기존 KPI와 보조 차트는 항상 표시한다.
    show_kpi = True
    show_charts = True

    py, pq = prev_quarter(
        year,
        quarter,
    )

    st.markdown(
        f"""
        <div style="
            margin-top: 2rem;
            padding: 12px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            font-size: 11px;
            color: rgba(255, 255, 255, 0.7);
        ">
            <strong style="color: #CBF1FF;">
                {t("period")}
            </strong>
            <br>
            {t("current_period")}: {year} {quarter}
            <br>
            {t("previous_period")}: {py} {pq}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button(
        t("clear_cache"),
        help=t("clear_cache_help"),
    ):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()


# ════════════════════════════════════════════════════════════════
# 4. 경로 계산 및 데이터 로드
# ════════════════════════════════════════════════════════════════
paths = build_paths(
    cfg,
    year,
    quarter,
)

_actual_expense_path = paths.get(
    "actual_expense",
    "",
)

NOTES_FILE = paths["notes_file"]

(
    df_mpf_prev_raw,
    df_mpf_curr_raw,
    df_vnb_res_raw,
    df_vnb_curr_raw,
    df_vnb_prev_raw,
    df_vnb_curr_full_raw,
    df_vnb_prev_full_raw,
    df_comm_curr_raw,
    df_comm_prev_raw,
    df_exp_curr_raw,
) = load_all_data(
    year,
    quarter,
    paths,
    _mtime=_paths_mtime(paths),
)


# ════════════════════════════════════════════════════════════════
# 5. 통화 변환
# ════════════════════════════════════════════════════════════════
_curr_end = quarter_end_date(
    year,
    quarter,
)

_cq_df = get_vnb_cq(
    df_vnb_curr_full_raw,
    _curr_end,
)

_cq_vnb = (
    float(_cq_df["VNB"].sum())
    if not _cq_df.empty
    else 0.0
)

_cq_anp = (
    float(_cq_df["ANP"].sum())
    if not _cq_df.empty
    else 0.0
)

_cq_row = pd.DataFrame([
    {
        "STEP": "CQ",
        "VNB": _cq_vnb,
        "ANP": _cq_anp,
    }
])

df_vnb_res_raw = pd.concat(
    [
        df_vnb_res_raw,
        _cq_row,
    ],
    ignore_index=True,
)

df_vnb_res_conv = convert_currency(
    df_vnb_res_raw,
    display_currency,
    fx_rate,
)

_CT_PQ_ANP = float(
    df_vnb_res_conv.loc[
        df_vnb_res_conv["STEP"] == "PQ",
        "ANP",
    ].sum()
)

_CT_CQ_ANP = (
    float(
        df_vnb_res_conv.loc[
            df_vnb_res_conv["STEP"] == "CQ",
            "ANP",
        ].sum()
    )
    if "CQ" in df_vnb_res_conv["STEP"].values
    else 0.0
)

df_vnb_curr_conv = convert_currency(
    df_vnb_curr_raw,
    display_currency,
    fx_rate,
)

df_vnb_prev_conv = convert_currency(
    df_vnb_prev_raw,
    display_currency,
    fx_rate,
)

df_mpf_prev_conv = convert_currency(
    df_mpf_prev_raw,
    display_currency,
    fx_rate,
    is_mpf=True,
    fx_krw=PREV_FX_RATE,
)

df_mpf_curr_conv = convert_currency(
    df_mpf_curr_raw,
    display_currency,
    fx_rate,
    is_mpf=True,
    fx_krw=CURR_FX_RATE,
)


fx_unit_suffix = (
    "$"
    if display_currency == "USD"
    else "₩"
)

unit_label = t(
    "unit_millions",
    symbol=fx_unit_suffix,
)

period_label = f"{year} {quarter}"


pg_opts = (
    ["Company Total"]
    + sorted(
        df_vnb_curr_raw[
            "PRODUCT_GROUP1"
        ].dropna().unique().tolist()
    )
)

ch_opts = (
    ["Company Total"]
    + sorted(
        df_vnb_curr_raw[
            "CHANNEL"
        ].dropna().unique().tolist()
    )
)


# Summary MultiIndex 형식
_TH_CENTER = [
    {
        "selector": "th",
        "props": [
            ("text-align", "center"),
        ],
    }
]

SUMMARY_FMT = {
    ("PREV", "ANP"): lambda x: format_value(
        x,
        "amount",
    ),
    ("PREV", "VNB"): lambda x: format_value(
        x,
        "amount",
    ),
    ("PREV", "VNB%"): lambda x: format_value(
        x,
        "percent",
    ),
    ("CURR", "ANP"): lambda x: format_value(
        x,
        "amount",
    ),
    ("CURR", "VNB"): lambda x: format_value(
        x,
        "amount",
    ),
    ("CURR", "VNB%"): lambda x: format_value(
        x,
        "percent",
    ),
    ("DIFF", "ANP"): lambda x: format_value(
        x,
        "diff_amount",
    ),
    ("DIFF", "VNB"): lambda x: format_value(
        x,
        "diff_amount",
    ),
    ("DIFF", "VNB%"): lambda x: format_value(
        x,
        "diff_percent",
    ),
}


# ════════════════════════════════════════════════════════════════
# 6. 상단 헤더
# ════════════════════════════════════════════════════════════════
render_top_header(
    title=t("app_title"),
    subtitle=t("app_subtitle"),
    period_label=period_label,
    currency=display_currency,
)


# ════════════════════════════════════════════════════════════════
# 7. HTML Report 및 탭 컨텍스트 구성
# ════════════════════════════════════════════════════════════════
html_report = HtmlReport(
    title=t("app_title"),
    subtitle=t("app_subtitle"),
    period=period_label,
    currency=display_currency,
    unit_label=unit_label,
)


ctx = SimpleNamespace(
    # 언어
    language=language,
    t=t,

    # HTML Export
    html_report=html_report,

    # 환경 및 경로
    cfg=cfg,
    paths=paths,
    NOTES_FILE=NOTES_FILE,

    # 기간 및 통화
    year=year,
    quarter=quarter,
    display_currency=display_currency,
    fx_rate=fx_rate,

    # 화면 옵션
    show_kpi=show_kpi,
    show_charts=show_charts,

    # Walk 설정
    STEP_ORDER=STEP_ORDER,

    # FX
    CURR_FX_RATE=CURR_FX_RATE,
    PREV_FX_RATE=PREV_FX_RATE,
    PLAN_FX_RATE=PLAN_FX_RATE,

    # 분석 옵션
    OTHER_LIMIT=OTHER_LIMIT,

    # Company Total ANP
    CT_PQ_ANP=_CT_PQ_ANP,
    CT_CQ_ANP=_CT_CQ_ANP,

    # VNB 데이터
    df_vnb_res_conv=df_vnb_res_conv,
    df_vnb_curr_conv=df_vnb_curr_conv,
    df_vnb_prev_conv=df_vnb_prev_conv,
    df_vnb_curr_full_raw=df_vnb_curr_full_raw,
    df_vnb_prev_full_raw=df_vnb_prev_full_raw,
    df_vnb_res_raw=df_vnb_res_raw,

    # MPF 데이터
    df_mpf_curr_conv=df_mpf_curr_conv,
    df_mpf_prev_conv=df_mpf_prev_conv,

    # Commission
    df_comm_curr_raw=df_comm_curr_raw,
    df_comm_prev_raw=df_comm_prev_raw,

    # Expense
    df_exp_curr_raw=df_exp_curr_raw,
    actual_expense_path=_actual_expense_path,

    # UI 형식
    unit_label=unit_label,
    fx_unit_suffix=fx_unit_suffix,
    period_label=period_label,
    pg_opts=pg_opts,
    ch_opts=ch_opts,
    SUMMARY_FMT=SUMMARY_FMT,
    TH_CENTER=_TH_CENTER,

    # 캐시 함수
    cached_filtered_walk=_cached_filtered_walk,
)


# ════════════════════════════════════════════════════════════════
# 8. 탭 렌더링
# ════════════════════════════════════════════════════════════════
page_tabs = st.tabs([
    t("tab_summary"),
    t("tab_sales_mix"),
    t("tab_demo"),
    t("tab_economic"),
    t("tab_commission"),
    t("tab_expense"),
])


with page_tabs[0]:
    tab_summary.render(ctx)


with page_tabs[1]:
    tab_sales_mix.render(ctx)


with page_tabs[2]:
    tab_demo.render(ctx)


with page_tabs[3]:
    tab_economic.render(ctx)


with page_tabs[4]:
    tab_commission.render(ctx)


with page_tabs[5]:
    tab_expense.render(ctx)


# ════════════════════════════════════════════════════════════════
# 9. HTML Export
# ════════════════════════════════════════════════════════════════
html_content = html_report.build()

st.divider()

_col_export, _ = st.columns([
    1,
    3,
])

with _col_export:
    st.download_button(
        label=t("download_html_report"),
        data=html_content.encode("utf-8"),
        file_name=(
            f"VNB_Walk_Analysis_"
            f"{year}_{quarter}_"
            f"{display_currency}_"
            f"{language}.html"
        ),
        mime="text/html",
        help=t("html_export_help"),
        type="primary",
        use_container_width=True,
    )


# ════════════════════════════════════════════════════════════════
# 10. Footer
# ════════════════════════════════════════════════════════════════
render_footer(t)