"""공용 백테스트/성과지표 유틸.

논문 결과(Sharpe, 변동성, MDD 등)와 직접 비교하기 위한 표준 지표 계산 함수.
모든 함수는 입력을 변경하지 않고 새 객체를 반환한다(불변성).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def annualized_return(returns: pd.Series, periods_per_year: int = TRADING_DAYS) -> float:
    r = returns.dropna()
    if r.empty:
        return float("nan")
    growth = (1.0 + r).prod()
    years = len(r) / periods_per_year
    return growth ** (1.0 / years) - 1.0 if years > 0 else float("nan")


def annualized_vol(returns: pd.Series, periods_per_year: int = TRADING_DAYS) -> float:
    return returns.dropna().std(ddof=1) * np.sqrt(periods_per_year)


def sharpe_ratio(
    returns: pd.Series, rf: float = 0.0, periods_per_year: int = TRADING_DAYS
) -> float:
    """rf 는 연율화된 무위험수익률(예: FRED DGS3MO/100)."""
    r = returns.dropna()
    excess = r - rf / periods_per_year
    sd = excess.std(ddof=1)
    if sd == 0 or np.isnan(sd):
        return float("nan")
    return np.sqrt(periods_per_year) * excess.mean() / sd


def sortino_ratio(
    returns: pd.Series, rf: float = 0.0, periods_per_year: int = TRADING_DAYS
) -> float:
    r = returns.dropna()
    excess = r - rf / periods_per_year
    downside = excess[excess < 0].std(ddof=1)
    if downside == 0 or np.isnan(downside):
        return float("nan")
    return np.sqrt(periods_per_year) * excess.mean() / downside


def max_drawdown(returns: pd.Series) -> float:
    """누적수익 곡선 기준 최대 낙폭(음수)."""
    r = returns.dropna()
    if r.empty:
        return float("nan")
    curve = (1.0 + r).cumprod()
    peak = curve.cummax()
    return (curve / peak - 1.0).min()


def calmar_ratio(returns: pd.Series, periods_per_year: int = TRADING_DAYS) -> float:
    mdd = abs(max_drawdown(returns))
    if mdd == 0 or np.isnan(mdd):
        return float("nan")
    return annualized_return(returns, periods_per_year) / mdd


def summary_stats(
    returns: pd.Series, rf: float = 0.0, periods_per_year: int = TRADING_DAYS
) -> dict[str, float]:
    """논문 비교용 핵심 지표 묶음."""
    return {
        "ann_return": annualized_return(returns, periods_per_year),
        "ann_vol": annualized_vol(returns, periods_per_year),
        "sharpe": sharpe_ratio(returns, rf, periods_per_year),
        "sortino": sortino_ratio(returns, rf, periods_per_year),
        "max_drawdown": max_drawdown(returns),
        "calmar": calmar_ratio(returns, periods_per_year),
    }


def comparison_table(
    paper: dict[str, float],
    reproduced: dict[str, float],
    extensions: dict[str, dict[str, float]] | None = None,
) -> pd.DataFrame:
    """논문값 vs 재현값 vs (확장값) 비교표 생성. delta(%) 자동 계산.

    paper       : 논문이 보고한 지표 {metric: value}
    reproduced  : in-sample 재현 지표
    extensions  : {"oos": {...}, "time_robust": {...}} 형태(선택)
    """
    rows = []
    metrics = list(paper.keys())
    for m in metrics:
        p = paper.get(m, np.nan)
        rep = reproduced.get(m, np.nan)
        delta = (rep - p) / p * 100 if p not in (0, None) and not np.isnan(p) else np.nan
        row = {"metric": m, "paper": p, "reproduced": rep, "delta_%": delta}
        if extensions:
            for ext_name, ext_vals in extensions.items():
                row[ext_name] = ext_vals.get(m, np.nan)
        rows.append(row)
    return pd.DataFrame(rows)
