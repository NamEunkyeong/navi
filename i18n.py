"""
i18n.py
───────
VNB Walk Analysis Dashboard의 Korean / English UI 문구를 관리한다.

사용 예시
---------
t = get_translator("Korean")
st.subheader(t("analysis_report"))

변수를 포함하는 문구:
t("vnb_walk_scope", scope="Company Total")
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


TRANSLATIONS: dict[str, dict[str, str]] = {
    "Korean": {
        # ── 공통 ──────────────────────────────────────────────
        "all": "All",
        "company_total": "Company Total",
        "none": "없음",
        "not_available": "N/A",
        "previous": "전분기",
        "current": "당분기",
        "plan": "Plan",
        "actual": "Actual",
        "model": "Model",
        "unit": "단위",
        "unit_millions": "Unit: Millions ({symbol}M)",
        "data_not_available": "데이터가 없습니다.",
        "file_not_available": "파일이 없습니다.",
        "filter": "Filter",
        "analysis_report": "📝 Analysis Report",
        "download_html_report": "⬇️ HTML Report 다운로드",
        "language": "Language",
        "korean": "Korean",
        "english": "English",
        "current_quarter_anp": "당분기 ANP",
        "current_quarter_vnb": "당분기 VNB",
        "vnb_margin": "VNB Margin",
        "vs_previous": "vs 전분기",

        # ── 상단 헤더 ─────────────────────────────────────────
        "app_title": "VNB Walk Analysis",
        "app_subtitle": "Value of New Business · Variance Analysis Dashboard",
        "sidebar_title": "📊 VNB Analytics",
        "sidebar_subtitle": "Value of New Business Walk",

        # ── 사이드바 ──────────────────────────────────────────
        "global_setting": "Global Setting",
        "display_currency": "Display Currency",
        "display_currency_help": "전체 데이터를 해당 통화로 환산하여 표시합니다.",
        "language_help": "대시보드 화면과 분석 보고서의 표시 언어를 선택합니다.",
        "time_selection": "Time Selection",
        "year": "Year",
        "quarter": "Quarter",
        "fx_rate": "FX Rate",
        "fx_rate_input": "1 USD = ? KRW",
        "period": "Period",
        "current_period": "Current",
        "previous_period": "Previous",
        "clear_cache": "🔄 캐시 초기화",
        "clear_cache_help": (
            "parquet 파일 변경 또는 .env(NAVI_STEP_ORDER 등) 수정 후 "
            "새로 로드할 때 사용하세요."
        ),

        # ── 탭 ────────────────────────────────────────────────
        "tab_summary": "📊 Summary",
        "tab_sales_mix": "🧩 Sales Mix",
        "tab_demo": "👥 Demo",
        "tab_economic": "📈 Economic",
        "tab_commission": "💰 Commission",
        "tab_expense": "🧾 Expense",

        # ── 필터 ──────────────────────────────────────────────
        "product_group": "Product Group",
        "product": "Product",
        "channel": "Channel",
        "channel_scope": "Channel / Scope",
        "select_channel": "Select Channel",
        "select_product": "Select Product",
        "scenario_currency": "Scenario Currency",

        # ── Summary ───────────────────────────────────────────
        "company_total_vnb_walk": "Company Total VNB Walk",
        "total_vnb_movement": "Total VNB Movement",
        "key_step_impact": "🔍 주요 Step Impact (Margin 기준)",
        "margin_impact_rank": "Margin Impact #{rank}",
        "refer_to_tab": "{emoji} {tab_name} 탭 참고",
        "channel_anp_margin": "🏢 채널별 ANP · Margin",
        "quarterly_performance": "Quarterly Performance Comparison",
        "product_group_performance": "Product Group Performance",

        # ── Sales Mix ─────────────────────────────────────────
        "vnb_walk_scope": "VNB Walk · {scope}",
        "channel_mix_analysis": "Channel Mix Analysis (ANP %)",
        "channel_mix_chart": "Channel Mix · Prev vs Curr",
        "product_portfolio_mix": "Product Portfolio Mix (ANP %) — PRODUCT",
        "product_mix_chart": "Product Mix · Prev vs Curr",
        "contract_type_mix": "Contract Type Mix (ANP %)",
        "contract_type_mix_chart": "Contract Type Mix · Prev vs Curr",
        "top_four_highlight": (
            "절대값 기준 변동폭이 큰 상위 4개 항목에 "
            "하이라이트가 적용되어 있습니다."
        ),

        # ── Demo ──────────────────────────────────────────────
        "demo_note": (
            "- **Note**: 아래 표의 ANP는 sales ratio 반영 전 "
            "MPF의 ADJ_ANP 값 기준"
        ),
        "detailed_product_mix": "Detailed Product Mix (PRODUCT_ITEM)",
        "average_ticket_size": "Average Ticket Size Analysis",
        "premium_term_distribution": "Premium Term Distribution",
        "age_group_distribution": "Age Group Distribution",
        "deferment_average": "Deferment Period — Average (DEFER_Y > 0)",
        "prev_avg_deferment": "Prev. Avg Deferment (yrs)",
        "curr_avg_deferment": "Curr. Avg Deferment (yrs)",
        "deferment_exclusion_note": (
            "거치기간이 0인 계약(즉시연금·비연금)은 제외하고 계산합니다."
        ),
        "no_deferment_contracts": (
            "거치기간이 있는 계약이 없습니다 (DEFER_Y = 0)."
        ),
        "top_15_product_note": (
            "전분기 대비 ANP 비중 변동폭(절대값) 상위 15개 상품만 "
            "표시합니다. 전체 목록은 아래 표를 참고하세요."
        ),

        # ── Economic ──────────────────────────────────────────
        "economic_scenario_caption": "전분기 대비 시나리오 금리 변동 현황",
        "interest_rate_scenario": "{currency} Interest Rate Scenario",
        "interest_rate_scenario_title": (
            "{currency} Interest Rate Scenario "
            "(1200M Projection) · {period}"
        ),
        "interest_rate_file_missing": "금리 파일 없음: {path}",
        "fa_spread_analysis": "FA Spread Analysis",
        "fa_spread_file_missing": "FA Spread 파일 없음: {path}",
        "fx_comparison": "Foreign Exchange Rate Comparison",
        "prev_quarter_avg": "Prev. Quarter (Avg)",
        "curr_quarter_avg": "Curr. Quarter (Avg)",
        "change_percent": "Change (%)",

        # ── Commission ────────────────────────────────────────
        "commission_rate_analysis": "Commission Rate Analysis",
        "commission_unit": "단위: % (commission rate)",
        "commission_highlight": (
            "절대값 기준 CQ-PLAN 편차 상위 4개에 "
            "하이라이트가 적용되어 있습니다."
        ),
        "commission_data_missing": "Commission 데이터가 없습니다.",

        # ── Expense ───────────────────────────────────────────
        "expense_variance_analysis": "Expense Variance Analysis",
        "expense_summary": "Expense Summary · {scope}",
        "expense_data_missing": "Expense 데이터가 없습니다.",
        "expense_note": (
            "- **ACQ_TOTAL** = ANP + SC + PNI  \n"
            "- **TOTAL** = ACQ_TOTAL + COMM  \n"
            "- **AFT_TAX** = (Actual - Model) × (1 - tax rate)  \n"
            "- **TAX** 는 withholding 반영 추정치"
        ),
        "expense_chart_title": "Expense · Actual vs Model by Category",

        # ── 노트 ──────────────────────────────────────────────
        "auto_draft_preview": "🤖 자동 분석 초안 미리보기",
        "apply_draft": "초안을 노트에 적용하기",
        "draft_applied": "초안이 노트에 적용되었습니다.",
        "current_insights": "Current Insights",
        "no_saved_note": (
            "저장된 분석 노트가 없습니다. 위 자동 초안을 적용하거나 "
            "아래에 직접 작성해주세요."
        ),
        "edit_analysis": "✍️ 분석 내용 작성/수정하기",
        "insight_details": "Insight Details",
        "insight_placeholder": "여기에 분석 결과를 입력하세요.",
        "save_update_report": "Save & Update Report",
        "report_updated": "리포트가 업데이트되었습니다.",

        # ── HTML Export ───────────────────────────────────────
        "html_export_help": (
            "현재 선택된 필터 결과를 기준으로 정적 HTML 보고서를 생성합니다. "
            "Plotly JavaScript가 포함되므로 인터넷 연결 없이 열 수 있습니다."
        ),
        "html_export_footer": "VNB Analytics에서 생성된 정적 HTML 보고서",

        # ── Footer ────────────────────────────────────────────
        "footer_dashboard": "VNB Walk Analysis Dashboard",
        "footer_powered_by": "Powered by Actuarial Analytics",
    },

    "English": {
        # ── Common ────────────────────────────────────────────
        "all": "All",
        "company_total": "Company Total",
        "none": "None",
        "not_available": "N/A",
        "previous": "Previous Quarter",
        "current": "Current Quarter",
        "plan": "Plan",
        "actual": "Actual",
        "model": "Model",
        "unit": "Unit",
        "unit_millions": "Unit: Millions ({symbol}M)",
        "data_not_available": "No data is available.",
        "file_not_available": "The file is not available.",
        "filter": "Filter",
        "analysis_report": "📝 Analysis Report",
        "download_html_report": "⬇️ Download HTML Report",
        "language": "Language",
        "korean": "Korean",
        "english": "English",
        "current_quarter_anp": "Current Quarter ANP",
        "current_quarter_vnb": "Current Quarter VNB",
        "vnb_margin": "VNB Margin",
        "vs_previous": "vs Previous Quarter",

        # ── Header ────────────────────────────────────────────
        "app_title": "VNB Walk Analysis",
        "app_subtitle": "Value of New Business · Variance Analysis Dashboard",
        "sidebar_title": "📊 VNB Analytics",
        "sidebar_subtitle": "Value of New Business Walk",

        # ── Sidebar ───────────────────────────────────────────
        "global_setting": "Global Setting",
        "display_currency": "Display Currency",
        "display_currency_help": (
            "Converts and displays all monetary values "
            "in the selected currency."
        ),
        "language_help": (
            "Select the display language for the dashboard "
            "and analysis reports."
        ),
        "time_selection": "Time Selection",
        "year": "Year",
        "quarter": "Quarter",
        "fx_rate": "FX Rate",
        "fx_rate_input": "1 USD = ? KRW",
        "period": "Period",
        "current_period": "Current",
        "previous_period": "Previous",
        "clear_cache": "🔄 Clear Cache",
        "clear_cache_help": (
            "Reload the dashboard after changing parquet files "
            "or configuration settings such as NAVI_STEP_ORDER."
        ),

        # ── Tabs ──────────────────────────────────────────────
        "tab_summary": "📊 Summary",
        "tab_sales_mix": "🧩 Sales Mix",
        "tab_demo": "👥 Demo",
        "tab_economic": "📈 Economic",
        "tab_commission": "💰 Commission",
        "tab_expense": "🧾 Expense",

        # ── Filters ───────────────────────────────────────────
        "product_group": "Product Group",
        "product": "Product",
        "channel": "Channel",
        "channel_scope": "Channel / Scope",
        "select_channel": "Select Channel",
        "select_product": "Select Product",
        "scenario_currency": "Scenario Currency",

        # ── Summary ───────────────────────────────────────────
        "company_total_vnb_walk": "Company Total VNB Walk",
        "total_vnb_movement": "Total VNB Movement",
        "key_step_impact": "🔍 Key Step Impact by Margin",
        "margin_impact_rank": "Margin Impact #{rank}",
        "refer_to_tab": "{emoji} Refer to the {tab_name} tab",
        "channel_anp_margin": "🏢 ANP and Margin by Channel",
        "quarterly_performance": "Quarterly Performance Comparison",
        "product_group_performance": "Product Group Performance",

        # ── Sales Mix ─────────────────────────────────────────
        "vnb_walk_scope": "VNB Walk · {scope}",
        "channel_mix_analysis": "Channel Mix Analysis (ANP %)",
        "channel_mix_chart": "Channel Mix · Previous vs Current",
        "product_portfolio_mix": "Product Portfolio Mix (ANP %) — PRODUCT",
        "product_mix_chart": "Product Mix · Previous vs Current",
        "contract_type_mix": "Contract Type Mix (ANP %)",
        "contract_type_mix_chart": "Contract Type Mix · Previous vs Current",
        "top_four_highlight": (
            "The four items with the largest absolute changes "
            "are highlighted."
        ),

        # ── Demo ──────────────────────────────────────────────
        "demo_note": (
            "- **Note**: ANP in the tables below is based on "
            "MPF ADJ_ANP before applying the sales ratio."
        ),
        "detailed_product_mix": "Detailed Product Mix (PRODUCT_ITEM)",
        "average_ticket_size": "Average Ticket Size Analysis",
        "premium_term_distribution": "Premium Term Distribution",
        "age_group_distribution": "Age Group Distribution",
        "deferment_average": "Deferment Period — Average (DEFER_Y > 0)",
        "prev_avg_deferment": "Previous Average Deferment (years)",
        "curr_avg_deferment": "Current Average Deferment (years)",
        "deferment_exclusion_note": (
            "Contracts with zero deferment, including immediate annuities "
            "and non-annuity contracts, are excluded."
        ),
        "no_deferment_contracts": (
            "No contracts with a deferment period are available "
            "(DEFER_Y = 0)."
        ),
        "top_15_product_note": (
            "Only the top 15 products by absolute change in ANP mix "
            "are displayed. Refer to the table below for the full list."
        ),

        # ── Economic ──────────────────────────────────────────
        "economic_scenario_caption": (
            "Comparison of scenario interest rates "
            "against the previous quarter"
        ),
        "interest_rate_scenario": "{currency} Interest Rate Scenario",
        "interest_rate_scenario_title": (
            "{currency} Interest Rate Scenario "
            "(1200M Projection) · {period}"
        ),
        "interest_rate_file_missing": (
            "Interest-rate scenario file not found: {path}"
        ),
        "fa_spread_analysis": "FA Spread Analysis",
        "fa_spread_file_missing": "FA spread file not found: {path}",
        "fx_comparison": "Foreign Exchange Rate Comparison",
        "prev_quarter_avg": "Previous Quarter (Average)",
        "curr_quarter_avg": "Current Quarter (Average)",
        "change_percent": "Change (%)",

        # ── Commission ────────────────────────────────────────
        "commission_rate_analysis": "Commission Rate Analysis",
        "commission_unit": "Unit: % (commission rate)",
        "commission_highlight": (
            "The four items with the largest absolute "
            "CQ-to-Plan variances are highlighted."
        ),
        "commission_data_missing": "No commission data is available.",

        # ── Expense ───────────────────────────────────────────
        "expense_variance_analysis": "Expense Variance Analysis",
        "expense_summary": "Expense Summary · {scope}",
        "expense_data_missing": "No expense data is available.",
        "expense_note": (
            "- **ACQ_TOTAL** = ANP + SC + PNI  \n"
            "- **TOTAL** = ACQ_TOTAL + COMM  \n"
            "- **AFT_TAX** = (Actual - Model) × (1 - tax rate)  \n"
            "- **TAX** is an estimate reflecting withholding tax."
        ),
        "expense_chart_title": "Expense · Actual vs Model by Category",

        # ── Notes ─────────────────────────────────────────────
        "auto_draft_preview": "🤖 Preview Automatically Generated Analysis",
        "apply_draft": "Apply Draft to Note",
        "draft_applied": "The draft has been applied to the note.",
        "current_insights": "Current Insights",
        "no_saved_note": (
            "No saved analysis note is available. Apply the draft above "
            "or enter the analysis manually below."
        ),
        "edit_analysis": "✍️ Write or Edit Analysis",
        "insight_details": "Insight Details",
        "insight_placeholder": "Enter the analysis results here.",
        "save_update_report": "Save & Update Report",
        "report_updated": "The report has been updated.",

        # ── HTML Export ───────────────────────────────────────
        "html_export_help": (
            "Generates a static HTML report using the currently selected "
            "filters. Plotly JavaScript is embedded, so the report can be "
            "opened without an internet connection."
        ),
        "html_export_footer": (
            "Static HTML report generated from VNB Analytics"
        ),

        # ── Footer ────────────────────────────────────────────
        "footer_dashboard": "VNB Walk Analysis Dashboard",
        "footer_powered_by": "Powered by Actuarial Analytics",
    },
}


def normalize_language(language: str | None) -> str:
    """언어 값을 Korean 또는 English로 정규화한다."""
    if str(language).strip().lower() in {
        "english",
        "en",
        "eng",
    }:
        return "English"

    return "Korean"


def translate(
    language: str,
    key: str,
    **kwargs: Any,
) -> str:
    """
    선택 언어의 문구를 반환한다.

    번역 키가 없으면 Korean 문구를 확인하고, Korean에도 없으면
    key 자체를 반환한다.
    """
    normalized_language = normalize_language(language)

    text = TRANSLATIONS.get(
        normalized_language,
        TRANSLATIONS["Korean"],
    ).get(
        key,
        TRANSLATIONS["Korean"].get(key, key),
    )

    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text

    return text


def get_translator(
    language: str,
) -> Callable[..., str]:
    """선택 언어에 고정된 번역 함수를 반환한다."""
    normalized_language = normalize_language(language)

    def t(key: str, **kwargs: Any) -> str:
        return translate(
            normalized_language,
            key,
            **kwargs,
        )

    return t