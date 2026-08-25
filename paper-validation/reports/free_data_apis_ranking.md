# 무료 금융 데이터 API 순위 (WRDS 대안)

> 작성: 2026-06 / 대상: 퀀트 논문 재현용 일별 주가·펀더멘털·매크로
> 평가 기준: **데이터 신뢰도/클리닝 · 히스토리 길이 · 수정주가 정확도 · 무료 한도 · 안정성**
> WRDS/CRSP 가 방학중 비활성일 때 쓸 수 있는 무료 소스 중에서 선정.

## 결론 (TL;DR)

| 순위 | API | 무료 한도 | 강점 | 용도 | 키 필요 |
|------|-----|-----------|------|------|---------|
| 🥇 **1** | **Tiingo** | 50/시간, 1,000/일, 500종목/월 | 30년+ 수정주가, 3개 거래소 교차 클리닝 | **일별 주가(재현 주력)** | ✅ 무료 |
| 🥈 2 | **Financial Modeling Prep** | 250/일 | SEC EDGAR 기반 재무제표·비율, 30년+ | 펀더멘털 | ✅ 무료 |
| 🥉 3 | **Finnhub** | 60/분 | 실시간 시세·펀더멘털, 99.99% uptime | 시세/펀더멘털 보조 | ✅ 무료 |
| 4 | **Twelve Data** | 800/일, 8/분 | 주식·FX·암호화폐 광범위 | 멀티에셋 | ✅ 무료 |
| 5 | **Alpha Vantage** | **25/일**, 5/분 | 기술지표 50종 | (한도 너무 작음) | ✅ 무료 |
| 6 | **Polygon.io** | 5/분 | 고품질 SIP 데이터 | (무료는 1~2년 히스토리뿐 → 백테스트 부적합) | ✅ 무료 |
| — | **FRED** | 사실상 무제한 | 공식 매크로(금리·CPI 등) | 매크로 (이미 셋업) | ✅ 무료 |
| — | **SEC EDGAR** | 무제한(10 req/s) | 공식 재무제표, 키 불필요 | 펀더멘털(공식) | ❌ 불필요 |
| — | **yfinance** | 비공식 | 키 불필요·즉시 | 빠른 탐색·폴백 | ❌ 불필요 |

## 왜 Tiingo 가 1순위인가

퀀트 논문 재현에서 일별 주가에 요구되는 것은 ① **배당·분할 반영된 수정주가(adjClose)**, ② **긴 히스토리**, ③ **클리닝 품질**입니다.

- **30년+ 히스토리**를 무료로 제공 — 대부분의 q-fin 논문 표본기간 커버.
- **3개 거래소 데이터를 교차 검증**하는 자체 클리닝 프레임워크로 오류·이상치 보정.
- 82,000+ 글로벌 증권, 37,000+ 미국/중국 주식, 45,000+ ETF/뮤추얼펀드.
- `adjClose`(분할+배당 조정)를 제공 → total-return 기반 수익률 계산이 정확.
- 무료 한도(시간당 50·일 1,000)는 **종목당 1요청 + parquet 캐싱**으로 충분.
  - 제약: 월 500 *unique* 종목. 광범위 cross-section 논문이면 캐시 누적으로 관리.

> ⚠️ 어떤 무료 API도 **CRSP 의 survivorship-bias-free + delisting return** 은 대체 못 합니다.
> Tiingo 는 "무료 중 최선의 근사"이며, 상장폐지 종목 편향은 리포트에 caveat 로 명시할 것.

## 탈락/주의 사유

- **Alpha Vantage**: 무료 한도가 500→100→**25회/일**로 급감. 분산 포트폴리오 한 번 돌리면 소진.
- **Polygon**: 데이터 품질은 최상급이나 무료는 **최근 1~2년**만 → 장기 백테스트 불가.
- **IEX Cloud**: 2024년 서비스 종료 → 후보 제외.
- **marketstack/FCS 등**: 무료 한도·품질이 위 후보 대비 열위.

## 권장 조합 (무료 풀스택)

```
일별 주가   →  Tiingo (adjClose)        # 1순위, 셋업 완료
펀더멘털    →  FMP  +  SEC EDGAR(공식)  # 교차 검증
매크로      →  FRED                      # 이미 셋업
빠른 탐색   →  yfinance                  # 키 불필요 폴백
```

## 셋업 상태

- `shared/data_loader.py` 에 **Tiingo 로더 추가 완료** (`source="tiingo"` 또는 `"auto"`).
- `.env` 에 `TIINGO_API_KEY` 칸 추가, `PRIMARY_EQUITY_SOURCE=auto` 로 설정.
- **사용자는 Tiingo 가입 후 키를 `.env` 에 붙여넣기만 하면 즉시 동작.**

## 출처

- [Tiingo — Pricing](https://www.tiingo.com/about/pricing) · [EOD 문서](https://www.tiingo.com/documentation/end-of-day)
- [Best Financial Data APIs in 2026 — nb-data](https://www.nb-data.com/p/best-financial-data-apis-in-2026)
- [Best Free Stock Market APIs 2026 — DEV Community](https://dev.to/nexgendata/best-free-stock-market-apis-and-data-tools-in-2026-a-developers-honest-comparison-1926)
- [Alpha Vantage 무료 한도 25/일 — AlphaLog](https://alphalog.ai/blog/alphavantage-api-complete-guide)
- [FMP 무료 250/일 vs Alpha Vantage — Find My Moat](https://www.findmymoat.com/vs/alpha-vantage-vs-financial-modeling-prep-fmp)
- [Finnhub](https://finnhub.io/) · [Polygon 무료 한도 — ksred](https://www.ksred.com/the-complete-guide-to-financial-data-apis-building-your-own-stock-market-data-pipeline-in-2025/)
- [QuantStart — Evaluating Data Coverage with Tiingo](https://www.quantstart.com/articles/evaluating-data-coverage-with-tiingo/)
