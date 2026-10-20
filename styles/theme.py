"""
styles/theme.py
───────────────
CSS :root 변수와 1:1 대응하는 Python 색상 상수.
style.css의 --P*, --T*, --N* 값과 항상 동기화 유지.
"""

# ── Primary (#003652 딥블루 계열) ─────────────────────────────────
PRIMARY = [
    "#003652",  # P0
    "#154865",  # P1
    "#226857",  # P2
    "#3185A9",  # P3
    "#47A3CB",  # P4
    "#61C2E5",  # P5
    "#8AD9F5",  # P6
    "#A8E7FF",  # P7
    "#CBF1FF",  # P8
    "#EFFBFF",  # P9
]

# ── Third / Mint (그린 계열) ──────────────────────────────────────
THIRD = [
    "#265B38",  # T0
    "#327147",  # T1
    "#469661",  # T2
    "#50AF70",  # T3
    "#5EC982",  # T4
    "#68DF8F",  # T5
    "#8FF5B1",  # T6  ← C_MINT
    "#B3FFCC",  # T7
    "#D3FFE2",  # T8
    "#F4FFF8",  # T9
]

# ── Support / Neutral (웜그레이 계열) ────────────────────────────
SUPPORT = [
    "#3E3D35",  # N0
    "#4E4A46",  # N1
    "#67625B",  # N2
    "#7C766E",  # N3
    "#9C978F",  # N4
    "#C4BEB5",  # N5
    "#DDDBD5",  # N6
    "#EAE7E1",  # N7
    "#F5F2ED",  # N8  ← C_BEIGE
    "#FBFAF8",  # N9
]

# SECONDARY는 미사용이지만 하위 호환용으로 PRIMARY alias
SECONDARY = PRIMARY

# ── 자주 쓰는 alias (CSS :root 변수와 동일) ──────────────────────
C_DEEP_BLUE  = PRIMARY[0]   # var(--P0) #003652
C_LIGHT_BLUE = PRIMARY[8]   # var(--P8) #CBF1FF
C_MINT       = THIRD[6]     # var(--T6) #8FF5B1
C_BEIGE      = SUPPORT[8]   # var(--N8) #F5F2ED
C_WHITE      = "#FFFFFF"


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """#RRGGBB → rgba(r,g,b,alpha)"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
