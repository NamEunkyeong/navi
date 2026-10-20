"""
styles/utils.py
───────────────
Streamlit CSS 주입 및 Matplotlib 컬러맵 유틸리티.
"""
import streamlit as st
import matplotlib.colors as mcolors

from styles.theme import C_DEEP_BLUE, C_WHITE, C_MINT


def local_css(file_name: str) -> None:
    """CSS 파일을 읽어 Streamlit 페이지에 주입한다."""
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# 0을 중심으로 하는 발산형 컬러맵 (Deep Blue ← 0 → Mint)
cmap_custom = mcolors.LinearSegmentedColormap.from_list(
    "vnb_theme", [C_DEEP_BLUE, C_WHITE, C_MINT]
)


def get_normalized_gmap(data_series, vmin=None, vmax=None):
    """
    TwoSlopeNorm으로 0 기준 정규화한 gmap(0~1 배열)을 반환한다.
    background_gradient의 gmap 인자에 직접 전달한다.
    """
    actual_vmin = data_series.min() if vmin is None else vmin
    actual_vmax = data_series.max() if vmax is None else vmax

    # 0이 범위 안에 반드시 포함되도록 보정
    final_vmin = min(actual_vmin, -0.001)
    final_vmax = max(actual_vmax,  0.001)

    norm = mcolors.TwoSlopeNorm(vmin=final_vmin, vcenter=0, vmax=final_vmax)
    return data_series.apply(norm)


# 헤더 가운데 정렬 스타일
_HEADER_CENTER = [
    {"selector": "th", "props": [("text-align", "center")]},
    {"selector": "th.col_heading", "props": [("text-align", "center")]},
    {"selector": "th.row_heading", "props": [("text-align", "center")]},
]


def center_headers(styler):
    """Styler에 헤더 가운데 정렬을 적용하고 반환한다."""
    return styler.set_table_styles(_HEADER_CENTER, overwrite=False)
