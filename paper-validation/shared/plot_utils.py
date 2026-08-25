"""공용 Plotly 시각화 유틸.

검증 리포트(report.md)에 임베드할 인터랙티브 차트를 생성/저장한다.
저장 위치는 호출 측에서 papers/<논문>/results/... 로 지정.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def equity_curves(returns_dict: dict[str, pd.Series], title: str = "Cumulative Return") -> go.Figure:
    """전략별 누적수익 곡선. {label: returns_series}."""
    fig = go.Figure()
    for label, r in returns_dict.items():
        curve = (1.0 + r.dropna()).cumprod()
        fig.add_trace(go.Scatter(x=curve.index, y=curve.values, mode="lines", name=label))
    fig.update_layout(
        title=title, xaxis_title="Date", yaxis_title="Growth of $1", template="plotly_white"
    )
    return fig


def comparison_bar(table: pd.DataFrame, metric_col: str = "metric") -> go.Figure:
    """comparison_table 결과를 막대그래프로. paper vs reproduced (+확장)."""
    fig = go.Figure()
    value_cols = [c for c in table.columns if c not in (metric_col, "delta_%")]
    for col in value_cols:
        fig.add_trace(go.Bar(name=col, x=table[metric_col], y=table[col]))
    fig.update_layout(
        barmode="group", title="Paper vs Reproduced vs Extensions",
        xaxis_title="Metric", yaxis_title="Value", template="plotly_white",
    )
    return fig


def drawdown_curve(returns: pd.Series, title: str = "Drawdown") -> go.Figure:
    r = returns.dropna()
    curve = (1.0 + r).cumprod()
    dd = curve / curve.cummax() - 1.0
    fig = go.Figure(go.Scatter(x=dd.index, y=dd.values, fill="tozeroy", name="Drawdown"))
    fig.update_layout(
        title=title, xaxis_title="Date", yaxis_title="Drawdown", template="plotly_white"
    )
    return fig


def save(fig: go.Figure, path: str | Path) -> Path:
    """HTML(인터랙티브) + 가능하면 PNG(정적) 로 저장. 경로 반환."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    html_path = path.with_suffix(".html")
    fig.write_html(str(html_path))
    try:
        fig.write_image(str(path.with_suffix(".png")))  # kaleido 필요
    except Exception:
        pass  # 정적 이미지는 선택사항 — 실패해도 HTML 은 남음
    return html_path
