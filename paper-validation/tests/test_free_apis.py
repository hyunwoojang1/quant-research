"""무료 금융 API 셋업 점검.

키가 없으면 '키를 넣으면 동작' 안내(SKIP), 키가 있으면 실제 호출(PASS/FAIL).
WRDS 미사용 기간용 대안 소스(Tiingo 등) + auto 폴백을 검증한다.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from shared import data_loader as dl  # noqa: E402
from shared import backtest_utils as bt  # noqa: E402

T0, T1 = "2023-01-01", "2023-03-31"


def check_tiingo() -> str:
    if not os.getenv("TIINGO_API_KEY"):
        return "SKIP (TIINGO_API_KEY 미설정 — https://www.tiingo.com 가입 후 .env 에 키 입력)"
    df = dl.load_equity(["AAPL", "MSFT"], T0, T1, source="tiingo", use_cache=False)
    aapl = df[df.ticker == "AAPL"].set_index("date")["ret"]
    sharpe = bt.summary_stats(aapl)["sharpe"]
    return f"PASS (rows={len(df)}, AAPL Sharpe={sharpe:.2f}, adjClose 사용)"


def check_auto() -> str:
    src = "tiingo" if os.getenv("TIINGO_API_KEY") else "yfinance"
    df = dl.load_equity(["AAPL"], T0, T1, source="auto", use_cache=False)
    return f"PASS (auto→{src}, rows={len(df)})"


def check_fred() -> str:
    if not os.getenv("FRED_API_KEY"):
        return "SKIP (FRED_API_KEY 미설정)"
    df = dl.load_macro(["DGS3MO"], T0, T1, use_cache=False)
    return f"PASS (rows={len(df)})"


def main() -> int:
    checks = {
        "Tiingo (1순위 주가)": check_tiingo,
        "auto 폴백": check_auto,
        "FRED (매크로)": check_fred,
    }
    print("=" * 60)
    print(" 무료 금융 API 셋업 점검")
    print("=" * 60)
    failed = False
    for name, fn in checks.items():
        try:
            status = fn()
        except Exception as e:  # noqa: BLE001
            status = f"FAIL: {type(e).__name__}: {e}"
            failed = True
        print(f"  {name:22s}: {status}")
    print("=" * 60)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
