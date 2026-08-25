# quant-research

Quantitative finance research — empirical analysis notebooks and a paper-validation framework.

## Structure

### [`wrds/`](wrds) — Firm-level analysis on WRDS (CRSP · Compustat)
Empirical notebooks using Wharton Research Data Services:
- **PER 시차변화 분석** — how P/E ratios respond to earnings announcements over time; entity mapping across identifier systems (PERMNO/GVKEY/CUSIP) and share-class aggregation
- **배당성과·수익성 관계분석** — relationship between dividend yield and firm profitability

### [`moat-analysis/`](moat-analysis) — Semiconductor moat analysis (INTC vs NVDA)
Fundamental comparison of economic moats in the semiconductor industry using financial-statement time series.

### [`paper-validation/`](paper-validation) — Paper replication & validation framework
Infrastructure for reproducing published quant papers with free/accessible data sources:
- Shared modules: `backtest_utils.py`, `data_loader.py` (WRDS → Tiingo → yfinance fallback chain), `plot_utils.py`
- Paper deep-dives (Korean): Diffusion-VAE for factor modeling (2023), Transformer-DRL + Black-Litterman portfolio construction (2024)
- `reports/free_data_apis_ranking.md` — practical ranking of free financial data APIs

## Setup

```bash
cd paper-validation
cp .env.example .env   # fill in your own API keys
pip install -r requirements.txt
```

WRDS notebooks require a [WRDS account](https://wrds-www.wharton.upenn.edu/) (academic access).

## Related

- [DS-440](https://github.com/hyunwoojang1/DS-440) — MHIDSS, a multi-horizon investment decision support system built on these research foundations
- [finance-platform](https://github.com/hyunwoojang1/finance-platform) — personal finance platform where research notes get operationalized
