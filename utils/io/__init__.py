"""
utils/io/ — 설정(.env) 로드 및 데이터 로드.

예전에는 이 전부가 utils/io.py 파일 하나(약 950줄)에 들어있었다. 관심사별로
아래 모듈로 나누었다:

    config.py         — .env 로드(load_config), 경로 계산(build_paths), 분기 헬퍼
    commission.py      — lob-mapping 로드, 통합 commission.xlsx 파싱
    mpf.py              — MPF(trad/isp/var parquet) 로더
    vnb.py               — VNB(vnb.parquet) 필터링 헬퍼 (get_vnb_cq 등)
    loader.py             — 메인 로더(load_all_data) — 위 모듈들을 조합
    generic_table.py       — Prophet 제네릭 테이블(.fac) 로더
    filtered_walk.py        — 필터 반영 VNB Walk 동적 생성

기존 코드 호환성
────────────────
`from utils.io import load_config, build_paths, ...` 처럼 예전 단일 파일
기준으로 작성된 import 구문이 그대로 동작하도록 여기서 공개 API를 전부
재노출한다. 새로 코드를 작성할 때는 필요한 서브모듈에서 직접 가져오는 것도
가능하다 (예: `from utils.io.config import build_paths`).
"""
from .config import (
    load_config,
    parse_current_quarter,
    build_paths,
    quarter_to_month,
    quarter_end_date,
    prev_quarter,
)
from .commission import load_commission_merged, load_commission_data
from .vnb import get_vnb_cq
from .loader import _paths_mtime, load_all_data
from .generic_table import load_generic_table
from .filtered_walk import build_filtered_walk

__all__ = [
    "load_config",
    "parse_current_quarter",
    "build_paths",
    "quarter_to_month",
    "quarter_end_date",
    "prev_quarter",
    "load_commission_merged",
    "load_commission_data",
    "get_vnb_cq",
    "_paths_mtime",
    "load_all_data",
    "load_generic_table",
    "build_filtered_walk",
]
