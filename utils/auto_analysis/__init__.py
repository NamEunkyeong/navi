"""
utils/auto_analysis/ — 탭별 자동 분석 초안(draft) 생성.

표와 차트 데이터를 보고 분석 리포트 초안을 자동 생성한다.
사용자는 초안을 그대로 쓰거나, 텍스트 영역에서 수정해 저장할 수 있다.

설계 원칙
─────────
- 탭마다 별도 모듈로 분리한다 (summary.py / sales_mix.py / demo.py /
  commission.py / expense.py). 공통 포맷팅 헬퍼는 _common.py에 모은다.
- 함수는 dict/DataFrame 입력만 받고 외부 의존을 최소화한다.
- 출력은 markdown 호환 plain text. (st.text_area 편집 가능)

기존 코드 호환성
────────────────
`from utils.auto_analysis import generate_summary_draft` 처럼 예전 단일
파일(utils/auto_analysis.py) 기준으로 작성된 import 구문이 그대로 동작하도록
여기서 모든 generate_*_draft 함수를 재노출한다.
"""
from .summary import generate_summary_draft
from .sales_mix import generate_sales_mix_draft
from .demo import generate_demo_draft
from .commission import generate_commission_draft
from .expense import generate_expense_draft

__all__ = [
    "generate_summary_draft",
    "generate_sales_mix_draft",
    "generate_demo_draft",
    "generate_commission_draft",
    "generate_expense_draft",
]
