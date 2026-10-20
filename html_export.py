"""
html_export.py
──────────────
Streamlit VNB Dashboard에서 생성된 Plotly 차트, DataFrame,
KPI 및 Markdown 분석 내용을 인터넷 연결 없이 열 수 있는
단일 HTML 파일로 변환한다.

각 Streamlit 탭은 다운로드한 HTML에서도 실제 클릭 가능한
탭으로 구분된다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from typing import Any

import markdown
import pandas as pd


@dataclass
class HtmlReport:
    """
    HTML Export 대상 섹션을 수집하고 단일 HTML을 생성한다.

    Streamlit 화면 자체를 저장하는 것이 아니라, 각 탭에서 이미 생성한
    Plotly Figure, DataFrame, KPI 및 Markdown 분석 내용을 재사용해
    독립 실행 가능한 HTML을 만든다.
    """

    title: str
    subtitle: str
    period: str
    currency: str
    unit_label: str = ""
    sections: list[dict[str, Any]] = field(default_factory=list)

    def add_tab(self, title: str) -> None:
        """새 HTML 탭을 시작한다."""
        self.sections.append({
            "type": "tab",
            "title": title,
        })

    def add_plotly(
        self,
        title: str,
        figure: Any,
        *,
        description: str = "",
    ) -> None:
        """Plotly Figure를 HTML Export 목록에 추가한다."""
        if figure is None:
            return

        self.sections.append({
            "type": "plotly",
            "title": title,
            "description": description,
            "figure": figure,
        })

    def add_dataframe(
        self,
        title: str,
        dataframe: pd.DataFrame | pd.Series,
        *,
        description: str = "",
        index: bool = True,
    ) -> None:
        """DataFrame 또는 Series를 HTML Export 목록에 추가한다."""
        if dataframe is None:
            return

        if isinstance(dataframe, pd.Series):
            dataframe = dataframe.to_frame()

        if dataframe.empty:
            return

        self.sections.append({
            "type": "dataframe",
            "title": title,
            "description": description,
            "dataframe": dataframe.copy(),
            "index": index,
        })

    def add_kpis(
        self,
        title: str,
        items: list[tuple[str, str, str | None]],
    ) -> None:
        """
        KPI 카드를 HTML Export 목록에 추가한다.

        Parameters
        ----------
        items:
            [
                ("KPI 이름", "현재 값", "변동 값"),
                ...
            ]
        """
        if not items:
            return

        self.sections.append({
            "type": "kpis",
            "title": title,
            "items": items,
        })

    def add_text(
        self,
        title: str,
        content: str,
        *,
        description: str = "",
    ) -> None:
        """
        Markdown 형식의 분석 보고서를 HTML Export 목록에 추가한다.

        ##, ###, **bold**, 목록 등의 Markdown 문법은
        최종 HTML에서 실제 서식으로 렌더링된다.
        """
        if content is None:
            return

        content = str(content).strip()

        if not content:
            return

        self.sections.append({
            "type": "text",
            "title": title,
            "description": description,
            "content": content,
        })

    def add_html(
        self,
        title: str,
        content: str,
        *,
        description: str = "",
    ) -> None:
        """이미 생성된 정적 HTML 콘텐츠를 추가한다."""
        if not content:
            return

        self.sections.append({
            "type": "html",
            "title": title,
            "description": description,
            "content": content,
        })

    @staticmethod
    def _format_cell(value: Any) -> str:
        """정적 HTML 표에 사용할 기본 셀 포맷."""
        if pd.isna(value):
            return ""

        if isinstance(value, bool):
            return str(value)

        if isinstance(value, int):
            return f"{value:,}"

        if isinstance(value, float):
            abs_value = abs(value)

            if abs_value >= 1_000:
                return f"{value:,.1f}"

            if abs_value >= 100:
                return f"{value:,.2f}"

            return f"{value:,.4f}".rstrip("0").rstrip(".")

        return str(value)

    def _dataframe_to_html(
        self,
        dataframe: pd.DataFrame,
        *,
        index: bool,
    ) -> str:
        """
        DataFrame을 HTML 표로 변환한다.

        MultiIndex 컬럼도 pandas 기본 HTML 변환 기능을 통해 유지한다.
        """
        formatted = dataframe.copy()

        for column in formatted.columns:
            formatted[column] = formatted[column].map(
                self._format_cell
            )

        return formatted.to_html(
            index=index,
            border=0,
            classes="report-table",
            na_rep="",
            escape=True,
        )

    @staticmethod
    def _markdown_to_html(content: str) -> str:
        """Markdown 분석 내용을 HTML로 변환한다."""
        return markdown.markdown(
            str(content).strip(),
            extensions=[
                "extra",
                "sane_lists",
                "nl2br",
            ],
            output_format="html5",
        )

    @staticmethod
    def _safe_tab_id(tab_index: int) -> str:
        """HTML element ID에 사용할 탭 ID를 생성한다."""
        return f"report-tab-{tab_index}"

    def _build_section_html(
        self,
        section: dict[str, Any],
        *,
        include_plotlyjs: bool,
    ) -> tuple[str, bool]:
        """
        개별 섹션의 HTML을 생성한다.

        Returns
        -------
        tuple[str, bool]
            생성된 HTML과 해당 섹션에서 Plotly JavaScript를
            포함했는지 여부.
        """
        section_type = section["type"]
        title = escape(str(section.get("title", "")))
        description = escape(
            str(section.get("description", ""))
        )

        description_html = (
            f'<p class="section-description">{description}</p>'
            if description
            else ""
        )

        if section_type == "plotly":
            figure = section["figure"]

            chart_html = figure.to_html(
                full_html=False,
                include_plotlyjs=(
                    True if include_plotlyjs else False
                ),
                config={
                    "displaylogo": False,
                    "responsive": True,
                    "scrollZoom": False,
                },
                default_width="100%",
            )

            return (
                f"""
                <section class="report-section">
                    <h2>{title}</h2>

                    {description_html}

                    <div class="chart-container">
                        {chart_html}
                    </div>
                </section>
                """,
                True,
            )

        if section_type == "dataframe":
            table_html = self._dataframe_to_html(
                section["dataframe"],
                index=section["index"],
            )

            return (
                f"""
                <section class="report-section">
                    <h2>{title}</h2>

                    {description_html}

                    <div class="table-container">
                        {table_html}
                    </div>
                </section>
                """,
                False,
            )

        if section_type == "kpis":
            cards: list[str] = []

            for label, value, delta in section["items"]:
                delta_html = (
                    f"""
                    <div class="kpi-delta">
                        {escape(str(delta))}
                    </div>
                    """
                    if delta
                    else ""
                )

                cards.append(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-label">
                            {escape(str(label))}
                        </div>

                        <div class="kpi-value">
                            {escape(str(value))}
                        </div>

                        {delta_html}
                    </div>
                    """
                )

            return (
                f"""
                <section class="report-section">
                    <h2>{title}</h2>

                    {description_html}

                    <div class="kpi-grid">
                        {''.join(cards)}
                    </div>
                </section>
                """,
                False,
            )

        if section_type == "text":
            rendered_content = self._markdown_to_html(
                section["content"]
            )

            return (
                f"""
                <section class="report-section analysis-section">
                    <h2>{title}</h2>

                    {description_html}

                    <div class="analysis-content">
                        {rendered_content}
                    </div>
                </section>
                """,
                False,
            )

        if section_type == "html":
            return (
                f"""
                <section class="report-section">
                    <h2>{title}</h2>

                    {description_html}

                    {section["content"]}
                </section>
                """,
                False,
            )

        return "", False

    def build(self) -> str:
        """
        등록된 모든 섹션을 실제 탭이 포함된 단일 HTML 문자열로 생성한다.
        """
        tabs: list[dict[str, Any]] = []
        current_tab: dict[str, Any] | None = None

        # add_tab() 이후에 등록된 섹션을 해당 탭에 묶는다.
        for section in self.sections:
            if section["type"] == "tab":
                current_tab = {
                    "title": str(section["title"]),
                    "sections": [],
                }

                tabs.append(current_tab)
                continue

            # add_tab() 호출 전에 콘텐츠가 등록된 경우를 위한 폴백
            if current_tab is None:
                current_tab = {
                    "title": "Dashboard",
                    "sections": [],
                }

                tabs.append(current_tab)

            current_tab["sections"].append(section)

        if not tabs:
            tabs.append({
                "title": "Dashboard",
                "sections": [],
            })

        tab_buttons: list[str] = []
        tab_panels: list[str] = []

        plotly_js_included = False

        for tab_index, tab in enumerate(tabs):
            tab_id = self._safe_tab_id(tab_index)
            active_class = " active" if tab_index == 0 else ""

            tab_buttons.append(
                f"""
                <button
                    class="tab-button{active_class}"
                    type="button"
                    data-tab-id="{tab_id}"
                    onclick="openReportTab('{tab_id}', this)"
                >
                    {escape(tab["title"])}
                </button>
                """
            )

            section_blocks: list[str] = []

            for section in tab["sections"]:
                section_html, included_plotly = (
                    self._build_section_html(
                        section,
                        include_plotlyjs=not plotly_js_included,
                    )
                )

                if section_html:
                    section_blocks.append(section_html)

                if included_plotly:
                    plotly_js_included = True

            panel_content = (
                "".join(section_blocks)
                if section_blocks
                else """
                <section class="report-section">
                    <p class="empty-message">
                        표시할 데이터가 없습니다.
                    </p>
                </section>
                """
            )

            tab_panels.append(
                f"""
                <div
                    id="{tab_id}"
                    class="tab-panel{active_class}"
                >
                    {panel_content}
                </div>
                """
            )

        content = f"""
        <nav class="tab-navigation">
            {''.join(tab_buttons)}
        </nav>

        <div class="tab-content">
            {''.join(tab_panels)}
        </div>
        """

        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        {escape(self.title)} - {escape(self.period)}
    </title>

    <style>
        * {{
            box-sizing: border-box;
        }}

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            margin: 0;
            padding: 0;
            color: #1f2937;
            background: #eef3f6;
            font-family:
                "Segoe UI",
                "Malgun Gothic",
                Arial,
                sans-serif;
        }}

        button {{
            font-family: inherit;
        }}

        .report-container {{
            width: min(1600px, calc(100% - 40px));
            margin: 24px auto 60px;
        }}

        .report-header {{
            position: relative;
            padding: 30px 34px;
            margin-bottom: 24px;
            overflow: hidden;
            color: #ffffff;
            background:
                linear-gradient(
                    135deg,
                    #003652 0%,
                    #075985 65%,
                    #0e7490 100%
                );
            border-radius: 14px;
            box-shadow:
                0 10px 28px rgba(0, 54, 82, 0.20);
        }}

        .report-header::after {{
            position: absolute;
            top: -60px;
            right: -60px;
            width: 240px;
            height: 240px;
            content: "";
            background:
                rgba(203, 241, 255, 0.10);
            border-radius: 50%;
        }}

        .report-header h1 {{
            position: relative;
            z-index: 1;
            margin: 0 0 8px;
            font-size: 30px;
            letter-spacing: -0.4px;
        }}

        .report-header .subtitle {{
            position: relative;
            z-index: 1;
            margin: 0 0 18px;
            color: #cbf1ff;
            font-size: 15px;
        }}

        .report-meta {{
            position: relative;
            z-index: 1;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .meta-item {{
            padding: 7px 11px;
            color: #eefaff;
            background:
                rgba(255, 255, 255, 0.12);
            border:
                1px solid rgba(255, 255, 255, 0.18);
            border-radius: 7px;
            font-size: 12px;
        }}

        /* HTML Report Tabs */

        .tab-navigation {{
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            gap: 5px;
            margin: 0 0 20px;
            padding: 7px;
            overflow-x: auto;
            background: #dfeaf0;
            border: 1px solid #ccdce4;
            border-radius: 11px;
            box-shadow:
                0 3px 10px rgba(15, 23, 42, 0.08);
        }}

        .tab-button {{
            flex: 0 0 auto;
            padding: 11px 18px;
            color: #315263;
            background: transparent;
            border: 0;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 650;
            white-space: nowrap;
            cursor: pointer;
            transition:
                color 0.15s ease,
                background 0.15s ease,
                box-shadow 0.15s ease;
        }}

        .tab-button:hover {{
            color: #003652;
            background:
                rgba(255, 255, 255, 0.68);
        }}

        .tab-button.active {{
            color: #ffffff;
            background: #003652;
            box-shadow:
                0 3px 8px rgba(0, 54, 82, 0.18);
        }}

        .tab-content {{
            width: 100%;
        }}

        .tab-panel {{
            display: none;
            width: 100%;
        }}

        .tab-panel.active {{
            display: block;
            animation:
                tab-fade-in 0.16s ease-in;
        }}

        @keyframes tab-fade-in {{
            from {{
                opacity: 0;
                transform: translateY(3px);
            }}

            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        /* Report Section */

        .report-section {{
            padding: 24px;
            margin-bottom: 20px;
            overflow: hidden;
            background: #ffffff;
            border: 1px solid #dae5eb;
            border-radius: 12px;
            box-shadow:
                0 3px 12px rgba(15, 23, 42, 0.06);
        }}

        .report-section > h2 {{
            margin: 0 0 17px;
            color: #003652;
            font-size: 18px;
            letter-spacing: -0.2px;
        }}

        .section-description {{
            margin: -8px 0 18px;
            color: #64748b;
            font-size: 12px;
        }}

        .empty-message {{
            margin: 0;
            color: #64748b;
            font-size: 13px;
            text-align: center;
        }}

        /* Plotly Chart */

        .chart-container {{
            width: 100%;
            min-height: 300px;
            overflow-x: auto;
        }}

        .chart-container .plotly-graph-div {{
            width: 100% !important;
        }}

        /* DataFrame */

        .table-container {{
            width: 100%;
            max-height: 700px;
            overflow: auto;
            border: 1px solid #dae5eb;
            border-radius: 8px;
        }}

        .report-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            white-space: nowrap;
        }}

        .report-table thead th {{
            position: sticky;
            top: 0;
            z-index: 2;
            padding: 10px 12px;
            color: #ffffff;
            text-align: center;
            background: #003652;
            border: 1px solid #1b5772;
        }}

        .report-table tbody th {{
            padding: 9px 12px;
            color: #003652;
            text-align: left;
            background: #eef5f8;
            border: 1px solid #dae5eb;
        }}

        .report-table td {{
            padding: 9px 12px;
            text-align: right;
            border: 1px solid #dae5eb;
        }}

        .report-table tbody tr:nth-child(even) td {{
            background: #f7fafc;
        }}

        .report-table tbody tr:hover td {{
            background: #eaf5f8;
        }}

        /* KPI */

        .kpi-grid {{
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(190px, 1fr));
            gap: 14px;
        }}

        .kpi-card {{
            padding: 18px;
            background:
                linear-gradient(
                    145deg,
                    #f9fcfd,
                    #eef6f8
                );
            border: 1px solid #d6e4e9;
            border-left: 5px solid #0e7490;
            border-radius: 9px;
        }}

        .kpi-label {{
            margin-bottom: 7px;
            color: #64748b;
            font-size: 12px;
            font-weight: 600;
        }}

        .kpi-value {{
            color: #003652;
            font-size: 23px;
            font-weight: 700;
        }}

        .kpi-delta {{
            margin-top: 5px;
            color: #475569;
            font-size: 12px;
        }}

        /* Markdown Analysis */

        .analysis-section {{
            border-left: 5px solid #0e7490;
        }}

        .analysis-content {{
            padding: 22px 26px;
            color: #334155;
            background: #f7fafc;
            border: 1px solid #dce7ec;
            border-radius: 9px;
            font-family:
                "Segoe UI",
                "Malgun Gothic",
                Arial,
                sans-serif;
            font-size: 14px;
            line-height: 1.75;
            word-break: keep-all;
            overflow-wrap: break-word;
        }}

        .analysis-content > :first-child {{
            margin-top: 0;
        }}

        .analysis-content > :last-child {{
            margin-bottom: 0;
        }}

        .analysis-content h1 {{
            margin: 4px 0 22px;
            padding-bottom: 11px;
            color: #003652;
            border-bottom: 2px solid #0e7490;
            font-size: 24px;
            line-height: 1.35;
        }}

        .analysis-content h2 {{
            margin: 6px 0 22px;
            padding-bottom: 10px;
            color: #003652;
            border-bottom: 2px solid #b9dce8;
            font-size: 21px;
            line-height: 1.4;
        }}

        .analysis-content h3 {{
            margin: 28px 0 10px;
            color: #075985;
            font-size: 17px;
            line-height: 1.4;
        }}

        .analysis-content h4 {{
            margin: 22px 0 8px;
            color: #0e5a75;
            font-size: 15px;
            line-height: 1.4;
        }}

        .analysis-content p {{
            margin: 8px 0 13px;
        }}

        .analysis-content strong {{
            color: #003652;
            font-weight: 700;
        }}

        .analysis-content ul,
        .analysis-content ol {{
            margin: 9px 0 16px;
            padding-left: 27px;
        }}

        .analysis-content li {{
            margin: 5px 0;
            padding-left: 3px;
        }}

        .analysis-content li::marker {{
            color: #0e7490;
            font-weight: 700;
        }}

        .analysis-content blockquote {{
            margin: 16px 0;
            padding: 12px 16px;
            color: #475569;
            background: #edf6f8;
            border-left: 4px solid #0e7490;
            border-radius: 0 7px 7px 0;
        }}

        .analysis-content code {{
            padding: 2px 5px;
            color: #075985;
            background: #e5eef2;
            border-radius: 4px;
            font-family: Consolas, monospace;
            font-size: 0.92em;
        }}

        .analysis-content pre {{
            padding: 14px 16px;
            overflow-x: auto;
            color: #e2e8f0;
            background: #163346;
            border-radius: 8px;
        }}

        .analysis-content pre code {{
            padding: 0;
            color: inherit;
            background: transparent;
        }}

        .analysis-content hr {{
            margin: 25px 0;
            border: 0;
            border-top: 1px solid #d5e1e7;
        }}

        .analysis-content table {{
            width: 100%;
            margin: 16px 0;
            border-collapse: collapse;
            font-size: 13px;
        }}

        .analysis-content th {{
            padding: 9px 11px;
            color: #ffffff;
            text-align: center;
            background: #003652;
            border: 1px solid #1b5772;
        }}

        .analysis-content td {{
            padding: 9px 11px;
            border: 1px solid #d5e1e7;
        }}

        .analysis-content tbody tr:nth-child(even) {{
            background: #eef5f8;
        }}

        .report-footer {{
            padding: 22px 0;
            color: #64748b;
            font-size: 11px;
            text-align: center;
        }}

        @media (max-width: 800px) {{
            .report-container {{
                width: calc(100% - 20px);
                margin-top: 10px;
            }}

            .report-header {{
                padding: 24px 20px;
            }}

            .report-header h1 {{
                font-size: 25px;
            }}

            .report-section {{
                padding: 16px;
            }}

            .analysis-content {{
                padding: 18px;
            }}

            .tab-button {{
                padding: 10px 14px;
                font-size: 13px;
            }}
        }}

        @media print {{
            body {{
                background: #ffffff;
            }}

            .report-container {{
                width: 100%;
                margin: 0;
            }}

            .tab-navigation {{
                display: none;
            }}

            .tab-panel {{
                display: block !important;
            }}

            .report-header,
            .report-section {{
                box-shadow: none;
            }}

            .report-section {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>

<body>
    <main class="report-container">
        <header class="report-header">
            <h1>
                {escape(self.title)}
            </h1>

            <p class="subtitle">
                {escape(self.subtitle)}
            </p>

            <div class="report-meta">
                <div class="meta-item">
                    Period: {escape(self.period)}
                </div>

                <div class="meta-item">
                    Currency: {escape(self.currency)}
                </div>

                <div class="meta-item">
                    {escape(self.unit_label)}
                </div>
            </div>
        </header>

        {content}

        <footer class="report-footer">
            Static HTML export generated from VNB Analytics
        </footer>
    </main>

    <script>
        function resizeVisiblePlotlyCharts(tabPanel) {{
            if (
                typeof Plotly === "undefined" ||
                !tabPanel
            ) {{
                return;
            }}

            const charts = tabPanel.querySelectorAll(
                ".plotly-graph-div"
            );

            charts.forEach(function(chart) {{
                try {{
                    Plotly.Plots.resize(chart);
                }} catch (error) {{
                    console.warn(
                        "Plotly chart resize failed:",
                        error
                    );
                }}
            }});
        }}

        function openReportTab(tabId, clickedButton) {{
            const panels = document.querySelectorAll(
                ".tab-panel"
            );

            const buttons = document.querySelectorAll(
                ".tab-button"
            );

            panels.forEach(function(panel) {{
                panel.classList.remove("active");
            }});

            buttons.forEach(function(button) {{
                button.classList.remove("active");
            }});

            const selectedPanel = document.getElementById(
                tabId
            );

            if (selectedPanel) {{
                selectedPanel.classList.add("active");
            }}

            if (clickedButton) {{
                clickedButton.classList.add("active");
            }}

            window.setTimeout(function() {{
                resizeVisiblePlotlyCharts(selectedPanel);

                window.dispatchEvent(
                    new Event("resize")
                );
            }}, 80);
        }}

        window.addEventListener(
            "load",
            function() {{
                const activePanel = document.querySelector(
                    ".tab-panel.active"
                );

                window.setTimeout(function() {{
                    resizeVisiblePlotlyCharts(activePanel);

                    window.dispatchEvent(
                        new Event("resize")
                    );
                }}, 150);
            }}
        );

        window.addEventListener(
            "resize",
            function() {{
                const activePanel = document.querySelector(
                    ".tab-panel.active"
                );

                resizeVisiblePlotlyCharts(activePanel);
            }}
        );
    </script>
</body>
</html>
"""