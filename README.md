# quant-research

Quantitative finance research — empirical analysis notebooks and a paper-validation framework.

## Structure

### [`moat-analysis/`](moat-analysis) — Semiconductor moat analysis (INTC vs NVDA)
How the semiconductor moat flipped from Intel to NVIDIA (2011–2025), measured with gross margin,
after-tax operating ROA, and SG&A efficiency on Compustat quarterly data.
**Reproducible without WRDS** — the comparison notebook runs off the committed 7,902-row CSV.

### [`wrds/`](wrds) — Event-study designs on WRDS (CRSP · Compustat)
Analysis notebooks with point-in-time-safe SQL (CCM link table, no ticker joins; TTM EPS effective
from announcement date). Running them requires WRDS academic access:
- **PER 시차변화 분석** — how the TTM P/E drifts in the 90 days after each earnings announcement (event-time design, AAPL pilot)
- **배당성과·수익성 관계분석** — annual dividend yield vs. ROA over a firm's lifecycle (AAPL pilot)

### [`paper-validation/`](paper-validation) — Paper replication & validation framework
Infrastructure for reproducing published quant papers with free/accessible data sources:
- Shared modules: `backtest_utils.py` (Sharpe/Sortino/MDD/Calmar + delta tables), `data_loader.py` (source-selectable equity loader: wrds | tiingo | yfinance, parquet-cached), `plot_utils.py`
- Paper deep-dives completed (Korean): Diffusion-VAE for factor modeling (2023), Transformer-DRL + Black-Litterman portfolio construction (2024) — implementation phase pending
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
