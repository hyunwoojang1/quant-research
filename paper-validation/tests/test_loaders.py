"""임시 통합 테스트: FRED / yfinance / WRDS 로더 + 성과지표 + 비교표.

실제 API 를 호출하므로 네트워크와 .env 자격증명이 필요하다.
각 섹션은 독립적으로 실행되어 하나가 실패해도 나머지는 계속된다.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

# shared 패키지 import 경로 추가
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shared import data_loader as dl  # noqa: E402
from shared import backtest_utils as bt  # noqa: E402

results: dict[str, str] = {}


def section(name: str, fn):
    print(f"\n{'='*60}\n[{name}]\n{'='*60}")
    try:
        fn()
        results[name] = "PASS"
        print(f"-> {name}: PASS")
    except Exception as e:  # noqa: BLE001
        results[name] = f"FAIL: {type(e).__name__}: {e}"
        print(f"-> {name}: FAIL")
        traceback.print_exc()


# ── 1) FRED ──
def test_fred():
    df = dl.load_macro(["DGS3MO", "CPIAUCSL"], "2023-01-01", "2023-06-30", use_cache=False)
    print(df.head())
    print("shape:", df.shape, "| series:", sorted(df["series_id"].unique()))
    assert not df.empty
    assert set(df["series_id"].unique()) == {"DGS3MO", "CPIAUCSL"}


# ── 2) yfinance ──
def test_yfinance():
    df = dl.load_equity(["AAPL", "MSFT"], "2023-01-01", "2023-03-31",
                        source="yfinance", use_cache=False)
    print(df.head())
    print("shape:", df.shape, "| tickers:", sorted(df["ticker"].unique()))
    assert not df.empty
    # 성과지표 계산 검증
    aapl = df[df["ticker"] == "AAPL"].set_index("date")["ret"]
    stats = bt.summary_stats(aapl)
    print("AAPL summary_stats:", {k: round(v, 4) for k, v in stats.items()})
    assert "sharpe" in stats


# ── 3) WRDS 연결 + CRSP ──
def test_wrds():
    conn = dl._get_wrds()
    print("WRDS connected. probing crsp.dsf ...")
    # 가벼운 probe 쿼리 (1행)
    probe = conn.raw_sql("SELECT date, permno, ret FROM crsp.dsf LIMIT 1", date_cols=["date"])
    print("probe row:\n", probe)
    # 실제 로더 경로
    df = dl.load_equity(["AAPL"], "2023-01-01", "2023-03-31",
                        source="wrds", use_cache=False)
    print(df.head())
    print("shape:", df.shape)
    assert not df.empty


# ── 4) 비교표 (순수 로직, 네트워크 불필요) ──
def test_comparison_table():
    paper = {"sharpe": 1.82, "ann_return": 0.21, "max_drawdown": -0.18}
    repro = {"sharpe": 1.74, "ann_return": 0.19, "max_drawdown": -0.22}
    ext = {"oos": {"sharpe": 1.31, "ann_return": 0.12, "max_drawdown": -0.30}}
    tbl = bt.comparison_table(paper, repro, ext)
    print(tbl.to_string(index=False))
    assert "delta_%" in tbl.columns


if __name__ == "__main__":
    section("comparison_table", test_comparison_table)
    section("FRED", test_fred)
    section("yfinance", test_yfinance)
    section("WRDS", test_wrds)

    print(f"\n{'#'*60}\nSUMMARY\n{'#'*60}")
    for k, v in results.items():
        print(f"  {k:20s}: {v}")
    failed = [k for k, v in results.items() if not v.startswith("PASS")]
    sys.exit(1 if failed else 0)
