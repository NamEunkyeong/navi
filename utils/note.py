"""
utils/note.py
─────────────
탭별 분석 노트를 저장하고 Streamlit UI로 렌더링한다.

기능
----
- 자동 분석 초안 미리보기
- 초안을 저장된 노트로 적용
- 사용자가 분석 내용 직접 수정
- Korean / English UI 지원
- 언어별 노트 분리 저장
- 최종 표시 분석 텍스트 반환
"""

from __future__ import annotations

from collections.abc import Callable
from html import escape
import json
import os

import streamlit as st


Translator = Callable[..., str]


# ════════════════════════════════════════════════════════════════
# 파일 I/O
# ════════════════════════════════════════════════════════════════
def load_notes(
    notes_file: str,
) -> dict:
    """노트 JSON 파일을 로드한다."""
    if not os.path.exists(notes_file):
        return {}

    try:
        with open(
            notes_file,
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except (
        json.JSONDecodeError,
        OSError,
    ):
        return {}


def save_notes(
    category: str,
    key: str,
    note: str,
    notes_file: str,
) -> None:
    """분석 노트를 JSON 파일에 저장한다."""
    notes = load_notes(notes_file)

    notes.setdefault(
        category,
        {},
    )[key] = note

    directory = os.path.dirname(
        notes_file
    )

    if directory:
        os.makedirs(
            directory,
            exist_ok=True,
        )

    with open(
        notes_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            notes,
            file,
            ensure_ascii=False,
            indent=4,
        )


# ════════════════════════════════════════════════════════════════
# 내부 헬퍼
# ════════════════════════════════════════════════════════════════
def _normalize_language(
    language: str | None,
) -> str:
    """언어 값을 Korean 또는 English로 정규화한다."""
    if str(language).strip().lower() in {
        "english",
        "en",
        "eng",
    }:
        return "English"

    return "Korean"


def _build_note_key(
    tab_name: str,
    keys: list,
    language: str,
) -> str:
    """
    언어별 노트 저장 키를 생성한다.

    Korean은 기존 저장 파일과의 호환성을 위해 기존 키를 유지한다.
    English에만 English 식별자를 추가한다.
    """
    scope_key = f"title_{'_'.join(map(str, keys))}"

    if language == "English":
        return (
            f"note_English_"
            f"{tab_name}_"
            f"{scope_key}"
        )

    return (
        f"note_"
        f"{tab_name}_"
        f"{scope_key}"
    )


def _fallback_text(
    language: str,
    korean: str,
    english: str,
) -> str:
    """번역 함수가 없을 때 사용할 폴백 문구."""
    return (
        english
        if language == "English"
        else korean
    )


# ════════════════════════════════════════════════════════════════
# UI 렌더링
# ════════════════════════════════════════════════════════════════
def render_note_section(
    tab_name: str,
    keys: list,
    NOTES_FILE: str,
    auto_draft: str | None = None,
    *,
    language: str = "Korean",
    t: Translator | None = None,
) -> str:
    """
    분석 메모 섹션을 렌더링하고 최종 분석 텍스트를 반환한다.

    반환 우선순위
    -------------
    1. 저장된 사용자 노트
    2. 자동 분석 초안
    3. 빈 문자열

    Parameters
    ----------
    tab_name:
        노트 카테고리 이름.

    keys:
        노트 식별을 위한 필터 값.

    NOTES_FILE:
        노트 JSON 파일 경로.

    auto_draft:
        자동 생성된 Markdown 분석 초안.

    language:
        Korean 또는 English.

    t:
        i18n.py의 번역 함수.
    """
    normalized_language = _normalize_language(
        language
    )

    all_notes = load_notes(
        NOTES_FILE
    )

    note_key = _build_note_key(
        tab_name,
        keys,
        normalized_language,
    )

    saved_note = (
        all_notes
        .get(tab_name, {})
        .get(note_key, "")
    )

    # ── UI 문구 ──────────────────────────────────────────────
    auto_draft_preview_label = (
        t("auto_draft_preview")
        if t
        else _fallback_text(
            normalized_language,
            "🤖 자동 분석 초안 미리보기",
            "🤖 Preview Automatically Generated Analysis",
        )
    )

    apply_draft_label = (
        t("apply_draft")
        if t
        else _fallback_text(
            normalized_language,
            "초안을 노트에 적용하기",
            "Apply Draft to Note",
        )
    )

    draft_applied_message = (
        t("draft_applied")
        if t
        else _fallback_text(
            normalized_language,
            "초안이 노트에 적용되었습니다.",
            "The draft has been applied to the note.",
        )
    )

    current_insights_label = (
        t("current_insights")
        if t
        else "Current Insights"
    )

    no_saved_note_message = (
        t("no_saved_note")
        if t
        else _fallback_text(
            normalized_language,
            (
                "저장된 분석 노트가 없습니다. "
                "위 자동 초안을 적용하거나 아래에 직접 작성해주세요."
            ),
            (
                "No saved analysis note is available. "
                "Apply the draft above or enter the analysis manually below."
            ),
        )
    )

    edit_analysis_label = (
        t("edit_analysis")
        if t
        else _fallback_text(
            normalized_language,
            "✍️ 분석 내용 작성/수정하기",
            "✍️ Write or Edit Analysis",
        )
    )

    insight_details_label = (
        t("insight_details")
        if t
        else "Insight Details"
    )

    insight_placeholder = (
        t("insight_placeholder")
        if t
        else _fallback_text(
            normalized_language,
            "여기에 분석 결과를 입력하세요.",
            "Enter the analysis results here.",
        )
    )

    save_button_label = (
        t("save_update_report")
        if t
        else "Save & Update Report"
    )

    report_updated_message = (
        t("report_updated")
        if t
        else _fallback_text(
            normalized_language,
            "리포트가 업데이트되었습니다.",
            "The report has been updated.",
        )
    )

    # ── 자동 분석 초안 ───────────────────────────────────────
    if auto_draft:
        with st.expander(
            auto_draft_preview_label,
            expanded=not bool(saved_note),
        ):
            st.markdown(auto_draft)

            if st.button(
                apply_draft_label,
                key=f"apply_{note_key}",
            ):
                save_notes(
                    tab_name,
                    note_key,
                    auto_draft,
                    NOTES_FILE,
                )

                st.success(
                    draft_applied_message
                )

                st.rerun()

    # ── 저장된 노트 출력 ─────────────────────────────────────
    if saved_note:
        st.markdown(
            f"""
            <div style="
                background-color: #F5F2ED;
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #003652;
            ">
                <h4 style="
                    margin-top: 0;
                    margin-bottom: 12px;
                    color: #003652;
                ">
                    {escape(current_insights_label)}
                </h4>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 저장된 노트는 Markdown으로 렌더링한다.
        # 기존 방식처럼 HTML <p> 안에 넣으면 **bold**, ## heading 등이
        # 일반 문자로 표시될 수 있다.
        st.markdown(saved_note)

    else:
        st.info(
            no_saved_note_message
        )

    st.write("")

    # ── 입력 및 수정 영역 ────────────────────────────────────
    with st.expander(
        edit_analysis_label,
        expanded=False,
    ):
        initial_value = (
            saved_note
            if saved_note
            else (auto_draft or "")
        )

        new_note = st.text_area(
            insight_details_label,
            value=initial_value,
            height=300,
            placeholder=insight_placeholder,
            key=f"input_{note_key}",
        )

        if st.button(
            save_button_label,
            key=f"btn_{note_key}",
        ):
            save_notes(
                tab_name,
                note_key,
                new_note,
                NOTES_FILE,
            )

            st.success(
                report_updated_message
            )

            st.rerun()

    # HTML Export에서 사용할 최종 분석 텍스트
    return saved_note or auto_draft or ""