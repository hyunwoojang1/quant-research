# Quant Research — 논문 검증 워크스페이스

퀀트 파이낸스 논문(q-fin.CP / q-fin.MF / q-fin.ST)을 발굴 → 분석 → 구현 → 검증하는
리서치 모노레포. `quant-research-validator` 스킬의 4-Phase 워크플로우와 연동된다.

## 폴더 구조

```
quant-research/
├── data/                     # 공용 데이터 (전체 논문 공유, parquet 캐시)
│   ├── market/               # 주가·ETF·인덱스 (WRDS/CRSP 우선, yfinance 폴백)
│   ├── macro/                # 금리·CPI 등 (FRED)
│   └── derivatives/          # 옵션체인·IV (WRDS/OptionMetrics)
│
├── papers/                   # 논문별 독립 폴더 (논문 선택 후 생성)
│   └── <연도>_<키워드>_<저자>/
│       ├── paper.pdf
│       ├── summary.md
│       ├── requirements.txt  # 논문별 전용 의존성
│       ├── models/
│       ├── results/{in_sample,out_of_sample,time_robustness}/
│       └── report.md
│
├── shared/                   # 논문 간 공용 유틸
│   ├── data_loader.py        # 주식(wrds|tiingo|yfinance 선택)·FRED 통합 로더 (+parquet 캐시)
│   ├── backtest_utils.py     # Sharpe·MDD 등 성과지표 + 비교표 생성
│   └── plot_utils.py         # Plotly 누적수익·드로다운·비교 차트
│
├── scripts/                  # 파이프라인 보조 스크립트
│   ├── discover_papers.py    # arXiv+Semantic Scholar 후보 발굴
│   ├── setup_papers.py       # 논문 폴더 스캐폴딩
│   └── make_paper_docx.py    # 논문 한글 상세해설 docx 생성
│
├── tests/                    # 데이터 로더·API 연결 검사 (네트워크 필요)
│
├── .env / .env.example       # FRED·WRDS 자격증명 (.env 는 커밋 금지)
├── requirements.txt          # 공용 의존성
└── README.md                 # 이 파일 (전체 현황 트래킹)
```

## 셋업

```bash
# 1. 가상환경
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# 2. 공용 의존성 설치
pip install -r requirements.txt

# 3. 자격증명 설정
copy .env.example .env          # Windows  (cp .env.example .env on *nix)
#   .env 에 FRED_API_KEY, WRDS_USERNAME 등 입력
#   WRDS 비밀번호는 ~/.pgpass 권장:
#     wrds-pgdata.wharton.upenn.edu:9737:wrds:<USER>:<PW>
```

## 데이터 소스 정책

**WRDS 사용 가능 기간(학기중)** 과 **방학중(무료 대안)** 을 분리한다.
`PRIMARY_EQUITY_SOURCE` 로 전환: `auto`(추천) | `wrds` | `tiingo` | `yfinance`.

| 용도 | 학기중 1순위 | 방학중 1순위(무료) | 폴백 |
|------|-------------|--------------------|------|
| in-sample 재현 (주식) | **WRDS / CRSP** | **Tiingo** (adjClose, 30년+) | yfinance |
| OOS·time-robustness | WRDS / CRSP | Tiingo | yfinance |
| 매크로 (금리·CPI) | **FRED** | FRED | — |
| 펀더멘털 | WRDS / Compustat | **FMP + SEC EDGAR** | — |
| 옵션 / IV | **WRDS / OptionMetrics** | (무료 대안 빈약) | — |

> 무료 API 순위·근거: [`reports/free_data_apis_ranking.md`](reports/free_data_apis_ranking.md)
>
> ⚠️ Tiingo·yfinance 는 CRSP 의 survivorship-bias-free·delisting return 을 대체하지 못한다.
> 재현 결과에 데이터 소스를 반드시 명시하고, 무료 소스로 재현한 수치는 생존편향 등
> 데이터 차이를 caveat 으로 표기한다.

### 무료 API 빠른 셋업 (방학중)
1. https://www.tiingo.com 가입 → Account → API → Token 복사
2. `.env` 의 `TIINGO_API_KEY=` 에 붙여넣기 (그게 전부 — `PRIMARY_EQUITY_SOURCE=auto` 가 자동 인식)
3. 검증: `python tests/test_free_apis.py`

## 논문 검증 현황

| # | 논문 | 연도 | Phase | 핵심 클레임 | 재현 결과 | 상태 |
|---|------|------|-------|-------------|-----------|------|
| 1 | Diffusion-VAE 팩터 모델 (Koa et al.) | 2023 | ②분석 | 생성모형 기반 팩터 추출이 선형 PCA 대비 우수 | — | 🟡 분석 완료·재현 대기 |
| 2 | Transformer-DRL + Black-Litterman (Sun et al.) | 2024 | ②분석 | DRL 뷰를 BL 사전분포에 주입해 포트폴리오 개선 | — | 🟡 분석 완료·재현 대기 |

> Phase: ①발굴 ②분석 ③구현 ④검증 / 상태: 🔲대기 🟡진행 ✅재현 ⚠️부분재현 ❌실패
>
> 분석 산출물: 각 논문 폴더의 `paper_detailed_KR.docx`(상세 해설) + `prerequisites_KR.md`(선수지식 정리)

### 진행 로그
- 2026-08: 논문 2편 Phase ② 완료 (한글 상세해설 + 선수지식 문서). Phase ③ 구현은 대기.

## 워크플로우 요약 (스킬과 연동)

1. **Phase 1 — 발굴**: arXiv + Semantic Scholar 로 최근 3년·인용수 상위 논문 카드 제시 → 선택
2. **Phase 2 — 분석**: 구조·수식·데이터·클레임·구현난이도 → `papers/<논문>/summary.md`
3. **Phase 3 — 구현**: 논문 폴더 + 전용 requirements + 모델 skeleton(수식 주석 연결)
4. **Phase 4 — 검증**: ①in-sample ②OOS(≥3종목) ③time(≥3구간) ④비교표+시각화 → `report.md`
