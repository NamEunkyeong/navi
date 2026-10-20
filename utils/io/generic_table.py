"""
utils/io/generic_table.py — Prophet 제네릭 테이블(.fac 등) 로더.

VARIABLE_TYPES/헤더(!N)/멀티 인덱스 규칙을 해석해서 Pandas DataFrame으로
변환한다 (load_generic_table). 금리 시나리오(.fac) 파일 로드에 사용된다.
"""
from __future__ import annotations

import io
import logging
import re
from pathlib import Path

import pandas as pd
from pandas.api.types import is_float_dtype, is_integer_dtype, is_string_dtype

logger = logging.getLogger(__name__)

PANDAS_FLOAT_DTYPE  = "Float64"
PANDAS_INT_DTYPE    = "Int64"
PANDAS_STRING_DTYPE = "string"


def load_generic_table(filepath: str | Path) -> pd.DataFrame:
    """
    Prophet 제네릭 테이블을 읽어 Pandas DataFrame으로 반환합니다.

    처리 규칙:
    - 파일의 첫 줄부터 탐색하여, 다음 조건을 처리합니다.
      * "VARIABLE_TYPES"로 시작하는 줄이 있으면 데이터 타입을 해석:
              - N → Float64
              - I → Int64
              - T 또는 T<숫자> → string
      * "!<숫자>"로 시작하는 줄이 있으면 해당 줄을 헤더(컬럼명)로 간주하고,
        바로 다음 줄부터 데이터를 읽습니다.
    - 헤더 이후 데이터 영역에서 `"` 또는 `!`로 시작하는 줄은 주석으로 간주하고 제외합니다.
    - VARIABLE_TYPES가 존재하면 그 정보를 기반으로 dtype을 지정합니다.
    - VARIABLE_TYPES가 없으면 Pandas의 기본 dtype 추론을 사용합니다.
    - "##END##" 및 "\x1a" 이후의 데이터는 무시합니다.
    - 처음 N("!N")개 컬럼을 멀티 인덱스로 설정합니다.
    - 첫 번째 컬럼(보통 "*" 마커 컬럼)은 결과에서 제거합니다.

    Args:
        filepath: 제네릭 테이블의 경로

    Returns:
        제네릭 테이블 데이터가 담긴 DataFrame

    Raises:
        ValueError: 파일 형식이 올바르지 않은 경우
    """
    raw = Path(filepath).read_bytes()

    # 파일 종료 마커(##END##, \x1a) 제거
    for key in (b"##END##", b"\x1a"):
        pos = raw.find(key)
        if pos != -1:
            raw = raw[:pos]

    # 텍스트 디코딩
    text = raw.strip().decode("unicode_escape", errors="ignore")
    lines = text.splitlines()

    if not lines:
        raise ValueError(f"파일이 비어있습니다: {filepath}")

    variable_types_line: str | None = None
    header_idx: int | None = None

    vt_pattern = re.compile(r"^\s*VARIABLE_TYPES\s*,", flags=re.IGNORECASE)
    header_pattern = re.compile(r"^\s*!\d*")

    # VARIABLE_TYPES와 헤더 탐지
    for idx, ln in enumerate(lines):
        if variable_types_line is None and vt_pattern.match(ln):
            variable_types_line = ln.strip()
        if header_pattern.match(ln):
            header_idx = idx
            break

    if header_idx is None:
        raise ValueError("헤더 라인('!<숫자>' 시작)을 찾을 수 없습니다.")

    # 헤더 라인(예: "!3,KEY1,KEY2,VAL1,VAL2,...")
    header_line = lines[header_idx].strip()
    data_lines = lines[header_idx + 1:]

    # 데이터에서 주석 라인 제거: '"' 또는 '!"' 로 시작
    data_lines = [ln for ln in data_lines if not (ln.startswith('"') or ln.startswith('!"'))]

    # !N 파싱 (인덱스 컬럼 개수)
    header_parts = [c.strip() for c in header_line.split(",")]
    if not header_parts:
        raise ValueError(f"헤더 라인이 비어있습니다: {filepath}")

    first_token = header_parts[0]
    if first_token == "!":
        index_count = 1
    else:
        m = re.match(r"^!(\d+)$", first_token)
        if not m:
            raise ValueError("헤더의 첫 토큰이 '!<숫자>' 형식이 아닙니다.")
        index_count = int(m.group(1))

    # CSV 본문 구성
    csv_body = header_line + "\n" + "\n".join(data_lines)

    # dtype 맵 구성
    dtype_map: dict[str, str] = {}

    def _dtype_from_variable_types(header_csv: str, spec_line: str) -> dict[str, str]:
        """
        VARIABLE_TYPES 스펙과 헤더를 매칭하여 dtype 맵을 생성합니다.
        - N → float64
        - I → Int64
        - T(숫자 포함) → string
        """
        cols = [c.strip() for c in header_csv.split(",")]
        tokens = [tok.strip().upper() for tok in spec_line.split(",", 1)[1].split(",")]
        limit = min(len(cols), len(tokens))

        mapping: dict[str, str] = {}
        for i in range(limit):
            col_name = cols[i]
            t = tokens[i]
            if t == "N":
                mapping[col_name] = PANDAS_FLOAT_DTYPE
            elif t == "I":
                mapping[col_name] = PANDAS_INT_DTYPE
            elif t.startswith("T"):
                mapping[col_name] = PANDAS_STRING_DTYPE
        return mapping

    # dtype 적용: VARIABLE_TYPES가 있으면 사용, 없으면 pandas 추론
    if variable_types_line:
        dtype_map = _dtype_from_variable_types(header_line, variable_types_line)

    # CSV 읽기
    df = pd.read_csv(io.StringIO(csv_body), keep_default_na=False, dtype=dtype_map)

    # VARIABLE_TYPES가 없어서 pandas 추론을 사용한 경우 타입 변환
    if not dtype_map:
        logger.debug("VARIABLE_TYPES 없음, pandas 추론 후 타입 변환 수행")
        for col in df.columns:
            if is_string_dtype(df[col]):
                df[col] = df[col].astype(PANDAS_STRING_DTYPE)
            elif is_integer_dtype(df[col]):
                df[col] = df[col].astype(PANDAS_INT_DTYPE)
            elif is_float_dtype(df[col]):
                df[col] = df[col].astype(PANDAS_FLOAT_DTYPE)

    # 인덱스 대상 컬럼명 계산
    if df.shape[1] < index_count:
        raise ValueError(f"인덱스로 지정해야 할 컬럼 수({index_count})가 실제 컬럼 수({df.shape[1]})보다 많습니다.")

    index_cols = list(df.columns[:index_count])

    # 멀티 인덱스 설정
    df = df.drop(columns=index_cols[0])
    if len(index_cols) > 1:
        df = df.set_index(index_cols[1:])

    logger.info(f"테이블 로드 완료: {Path(filepath).resolve()}, shape={df.shape}")

    return df
