<p align="center">
  <img src="./assets/navi.png" alt="NAVI" width="100%">
</p>

# navi — VNB Walk Analysis Dashboard (Demo)

분기별 VNB(Value of New Business) 변동을 채널·상품군·상품 단위로 분석하는
Streamlit 대시보드의 **데모 버전**입니다.

> ⚠️ 이 저장소의 데이터(`demo_data/`)는 `tools/make_demo_data.py`로 생성한
> **가상의 데모 데이터**입니다. 상품명·채널·금액·가정은 모두 임의로 만든 값이며
> 실제 회사 데이터와 무관합니다.

## 주요 기능

- **Summary** — Company Total VNB Walk(waterfall), Margin Impact 드릴다운, 채널별 ANP·Margin, 채널/상품군 비교
- **Sales Mix** — 상품군 × 채널 필터 기준 VNB Walk, 채널/상품/계약 형태 Mix 비교
- **Demo** — 상품 단위 VNB Walk, 납기/연령/거치기간 분포, 평균 Ticket Size
- **Economic** — 금리 시나리오(KRW/USD), FA Spread, 환율 비교
- **Commission** — 채널·상품별 commission rate(Plan/PQ/CQ) 비교
- **Expense** — 채널별 Expense Actual vs Model
- 탭별 자동 분석 초안(규칙 기반) + 분석 노트, HTML 보고서 다운로드

## 로컬 실행

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

별도 설정 없이 `demo_data/`를 읽습니다. (기본 분기: 2026 Q3, 선택 가능: 2026 Q1–Q4)

## 데모 데이터 다시 만들기

```bash
python tools/make_demo_data.py
```

고정 시드로 생성되므로 몇 번을 실행해도 같은 데이터가 나옵니다.
가상 상품·채널 구성은 스크립트 상단의 `PRODUCTS`, `CHANNELS`에서 바꿀 수 있습니다.

## 환경 설정 (선택)

경로·분기·환율 등은 `.env`로 바꿀 수 있습니다. 없으면 `utils/io/config.py`의
기본값(데모 데이터 기준)으로 동작합니다.

```bash
cp .env.example .env
```

## 프로젝트 구조

```
navi/
├── dashboard.py            # 페이지 설정 · 사이드바 · 데이터 로드 · 탭 디스패치
├── tabs/                   # 탭별 렌더링 (summary, sales_mix, demo, economic, commission, expense)
├── utils/
│   ├── io/                 # 설정 로드, 경로 계산, 데이터 로더
│   ├── auto_analysis/      # 탭별 자동 분석 초안
│   ├── processor.py        # 필터/집계
│   ├── charts.py / charts_extra.py / tables.py / components.py / note.py / util.py
├── styles/                 # 테마 색상, CSS
├── tools/make_demo_data.py # 데모 데이터 생성
├── demo_data/              # 가상 데모 데이터
└── .streamlit/config.toml
```

## 데이터 폴더 구조

```
demo_data/{YYYY}/{MM}/
├── outputs/    vnb.parquet, vnb-walk.parquet
├── dashboard/  trad.parquet, isp.parquet, var.parquet (MPF),
│               commission.xlsx, model-expense.csv, actual-expense.xlsx, lob-mapping.xlsx
└── scenarios/  fa-spread-{YYYYMM}.xlsx, VNBQ{n}_INT_RETURN_MR.fac
```
