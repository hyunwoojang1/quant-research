"""공용 데이터 로딩 유틸.

데이터 소스 우선순위:
  - in-sample 재현/주식: WRDS(CRSP) 우선, 실패 시 yfinance 폴백
  - 매크로: FRED
  - 옵션: WRDS(OptionMetrics) — 무료 폴백 사실상 없음

모든 결과는 data/ 하위에 parquet 으로 캐시되어 재실행 시 오프라인·결정적으로 동작한다.
자격증명은 .env / ~/.pgpass 에서만 읽고, 절대 코드에 하드코딩하지 않는다.
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# ── 경로 상수 ──
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MARKET_DIR = DATA / "market"
MACRO_DIR = DATA / "macro"
DERIV_DIR = DATA / "derivatives"

load_dotenv(ROOT / ".env")

_PRIMARY_EQUITY = os.getenv("PRIMARY_EQUITY_SOURCE", "auto").lower()


def _cache_path(directory: Path, key: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{key}.parquet"


def _read_cache(path: Path) -> pd.DataFrame | None:
    if path.exists():
        return pd.read_parquet(path)
    return None


# ── WRDS 커넥션 (지연 로딩) ──
_wrds_conn = None


def _get_wrds():
    """WRDS PostgreSQL 커넥션을 lazy 하게 생성.

    자격증명 우선순위: ~/.pgpass > .env(WRDS_USERNAME/PASSWORD).
    .env 에 비밀번호가 있으면 wrds_password 로 직접 전달해 비대화형 환경에서도
    프롬프트 없이 연결한다(.pgpass 가 있으면 그쪽이 우선됨).
    """
    global _wrds_conn
    if _wrds_conn is not None:
        return _wrds_conn
    import wrds  # 무거운 import 라 함수 안에서

    kwargs = {}
    if os.getenv("WRDS_USERNAME"):
        kwargs["wrds_username"] = os.getenv("WRDS_USERNAME")
    if os.getenv("WRDS_PASSWORD"):
        kwargs["wrds_password"] = os.getenv("WRDS_PASSWORD")
    if os.getenv("WRDS_HOSTNAME"):
        kwargs["wrds_hostname"] = os.getenv("WRDS_HOSTNAME")
    if os.getenv("WRDS_PORT"):
        kwargs["wrds_port"] = int(os.getenv("WRDS_PORT"))
    if os.getenv("WRDS_DBNAME"):
        kwargs["wrds_dbname"] = os.getenv("WRDS_DBNAME")

    # Preflight: 자격증명을 직접 검증해, 인증 실패 시 wrds 라이브러리의 대화형
    # 프롬프트(비대화형 환경에서 EOFError 로 뭉개짐) 대신 명확한 에러를 낸다.
    _preflight_wrds_auth(kwargs)

    _wrds_conn = wrds.Connection(**kwargs)
    return _wrds_conn


def _preflight_wrds_auth(kwargs: dict) -> None:
    """WRDS Postgres 자격증명을 직접 검증. 실패 시 RuntimeError 로 명확히 알린다.

    .pgpass 만으로 인증하는 경우(WRDS_PASSWORD 미설정)는 검증을 건너뛴다.
    """
    import urllib.parse

    import sqlalchemy as sa

    password = kwargs.get("wrds_password")
    if not password:
        return  # .pgpass 등 외부 인증에 위임

    user = kwargs.get("wrds_username", "")
    host = kwargs.get("wrds_hostname", "wrds-pgdata.wharton.upenn.edu")
    port = kwargs.get("wrds_port", 9737)
    dbname = kwargs.get("wrds_dbname", "wrds")
    uri = f"postgresql://{user}:{urllib.parse.quote(password)}@{host}:{port}/{dbname}"
    try:
        engine = sa.create_engine(
            uri, isolation_level="AUTOCOMMIT", connect_args={"sslmode": "require"}
        )
        with engine.connect() as conn:
            conn.execute(sa.text("SELECT 1"))
    except Exception as err:  # noqa: BLE001
        msg = str(err)
        if "PAM authentication failed" in msg or "password authentication failed" in msg:
            raise RuntimeError(
                f"WRDS 인증 실패: 사용자 '{user}' 의 비밀번호가 올바르지 않습니다. "
                ".env 의 WRDS_USERNAME/WRDS_PASSWORD 를 확인하세요."
            ) from err
        raise RuntimeError(f"WRDS 연결 실패: {msg[:200]}") from err


# ── 주식/ETF/인덱스 ──
def load_equity(
    tickers: list[str],
    start: str,
    end: str,
    *,
    source: str | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """일별 수정주가(adjusted close) 패널을 long 포맷으로 반환.

    반환 컬럼: [date, ticker, close, ret] (가능하면 delisting-adjusted return 포함)
    """
    src = (source or _PRIMARY_EQUITY).lower()
    key = f"equity_{src}_{'-'.join(sorted(tickers))}_{start}_{end}"
    cache = _cache_path(MARKET_DIR, key)
    if use_cache:
        cached = _read_cache(cache)
        if cached is not None:
            return cached

    # auto: 키가 있으면 tiingo, 없으면 yfinance 로 자동 폴백
    if src == "auto":
        src = "tiingo" if os.getenv("TIINGO_API_KEY") else "yfinance"
        key = f"equity_{src}_{'-'.join(sorted(tickers))}_{start}_{end}"
        cache = _cache_path(MARKET_DIR, key)
        if use_cache and (cached := _read_cache(cache)) is not None:
            return cached

    if src == "wrds":
        df = _load_equity_wrds(tickers, start, end)
    elif src == "tiingo":
        df = _load_equity_tiingo(tickers, start, end)
    elif src == "yfinance":
        df = _load_equity_yfinance(tickers, start, end)
    else:
        raise ValueError(f"알 수 없는 source: {src!r} (wrds | tiingo | yfinance | auto)")

    _validate_panel(df, key)
    df.to_parquet(cache, index=False)
    return df


def _load_equity_wrds(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """CRSP 일별 주가. ticker -> permno 매핑 후 survivorship-safe 하게 조회.

    NOTE: CRSP 는 ticker 재사용 이슈가 있으므로 실제 연구에서는 permno/cusip 으로
    고정하는 것이 정석. 여기서는 간단히 ticker 기반 조회 스켈레톤만 제공한다.
    """
    db = _get_wrds()
    tick_list = ",".join(f"'{t.upper()}'" for t in tickers)
    sql = f"""
        SELECT d.date, d.permno, n.ticker,
               d.prc, d.ret, d.shrout, d.cfacpr
        FROM crsp.dsf AS d
        JOIN crsp.dsenames AS n
          ON d.permno = n.permno
         AND d.date BETWEEN n.namedt AND n.nameendt
        WHERE n.ticker IN ({tick_list})
          AND d.date BETWEEN '{start}' AND '{end}'
        ORDER BY n.ticker, d.date
    """
    raw = db.raw_sql(sql, date_cols=["date"])
    # CRSP prc 는 음수면 bid/ask 평균(거래 없음) 표시 -> 절댓값 처리
    raw["close"] = raw["prc"].abs() / raw["cfacpr"].replace(0, pd.NA)
    out = raw.rename(columns={})[["date", "ticker", "close", "ret"]].copy()
    return out.reset_index(drop=True)


def _load_equity_tiingo(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Tiingo EOD 일별 주가 (무료 1순위 소스).

    수정주가(adjClose: 배당+분할 반영)를 close 로 사용해 total-return 기반 수익률을
    계산한다. 무료 티어: 시간당 50회 / 일 1,000회 / 월 500종목.
    티커 1개당 요청 1회이므로 결과는 parquet 으로 캐시해 재요청을 줄인다.
    자격증명은 .env 의 TIINGO_API_KEY 만 사용(하드코딩 금지).
    """
    import requests

    token = os.getenv("TIINGO_API_KEY")
    if not token:
        raise RuntimeError(
            "TIINGO_API_KEY 가 .env 에 없습니다. https://www.tiingo.com 가입 후 "
            "API 키를 .env 에 넣으면 바로 동작합니다."
        )

    frames = []
    headers = {"Content-Type": "application/json"}
    for t in tickers:
        url = f"https://api.tiingo.com/tiingo/daily/{t}/prices"
        params = {"startDate": start, "endDate": end, "token": token, "format": "json"}
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        if resp.status_code in (401, 403):
            raise RuntimeError(
                "Tiingo 인증 실패: TIINGO_API_KEY 가 비었거나 올바르지 않습니다. "
                "https://www.tiingo.com 가입 후 Account→API 의 토큰을 .env 에 정확히 넣으세요."
            )
        if resp.status_code == 404:
            raise ValueError(f"Tiingo: 티커 '{t}' 를 찾을 수 없습니다.")
        if resp.status_code == 429:
            raise RuntimeError("Tiingo 요청 한도 초과(시간당 50/일 1,000). 잠시 후 재시도하세요.")
        resp.raise_for_status()
        rows = resp.json()
        if not rows:
            raise ValueError(f"Tiingo: '{t}' 구간 데이터가 비어 있습니다({start}~{end}).")
        raw = pd.DataFrame(rows).sort_values("date")
        # adjClose = 배당·분할 조정 종가 → 연구용 수익률의 표준.
        # Tiingo 는 close 와 adjClose 를 모두 주므로, 컬럼명 중복을 피하려 명시적으로 구성한다.
        out = pd.DataFrame(
            {
                "date": pd.to_datetime(raw["date"]).dt.tz_localize(None),
                "ticker": t,
                "close": raw["adjClose"].to_numpy(),
            }
        )
        out["ret"] = out["close"].pct_change()
        frames.append(out)
    return pd.concat(frames, ignore_index=True)


def _load_equity_yfinance(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """yfinance 폴백. survivorship bias 있음 — 탐색/확장용으로만 사용 권장.

    종목별로 개별 다운로드해 yfinance 버전별 컬럼 구조(단일/MultiIndex) 차이를
    안전하게 흡수한다.
    """
    import yfinance as yf

    frames = []
    for t in tickers:
        raw = yf.download(t, start=start, end=end, auto_adjust=True, progress=False)
        if raw is None or raw.empty:
            continue
        # 최신 yfinance 는 단일 종목도 MultiIndex(컬럼) 를 반환 → 1단계로 평탄화
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        s = raw[["Close"]].rename(columns={"Close": "close"})
        s["ticker"] = t
        s = s.reset_index().rename(columns={"Date": "date", "index": "date"})
        s["ret"] = s["close"].pct_change()
        frames.append(s[["date", "ticker", "close", "ret"]])
    if not frames:
        raise ValueError(f"yfinance: {tickers} 다운로드 결과가 비어 있습니다.")
    return pd.concat(frames, ignore_index=True)


# ── 매크로 (FRED) ──
def load_macro(series_ids: list[str], start: str, end: str, *, use_cache: bool = True) -> pd.DataFrame:
    """FRED 시계열을 long 포맷 [date, series_id, value] 으로 반환."""
    key = f"macro_{'-'.join(sorted(series_ids))}_{start}_{end}"
    cache = _cache_path(MACRO_DIR, key)
    if use_cache:
        cached = _read_cache(cache)
        if cached is not None:
            return cached

    from fredapi import Fred

    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        raise RuntimeError("FRED_API_KEY 가 .env 에 설정되어 있지 않습니다.")
    fred = Fred(api_key=api_key)

    frames = []
    for sid in series_ids:
        s = fred.get_series(sid, observation_start=start, observation_end=end)
        f = s.rename("value").to_frame()
        f["series_id"] = sid
        f = f.reset_index().rename(columns={"index": "date"})
        frames.append(f[["date", "series_id", "value"]])
    df = pd.concat(frames, ignore_index=True)
    df.to_parquet(cache, index=False)
    return df


# ── 옵션 (WRDS OptionMetrics) ──
def load_option_chain(
    secid_or_ticker: str, start: str, end: str, *, use_cache: bool = True
) -> pd.DataFrame:
    """OptionMetrics IvyDB 일별 옵션 가격/IV. WRDS 전용 (무료 폴백 없음)."""
    key = f"opt_{secid_or_ticker}_{start}_{end}"
    cache = _cache_path(DERIV_DIR, key)
    if use_cache:
        cached = _read_cache(cache)
        if cached is not None:
            return cached

    db = _get_wrds()
    # secid 매핑은 optionm.securd 에서 ticker -> secid 로 해결 필요 (생략된 스켈레톤)
    sql = f"""
        SELECT date, secid, cp_flag, strike_price, best_bid, best_offer,
               impl_volatility, delta, gamma, vega, theta
        FROM optionm.opprcd
        WHERE secid = {secid_or_ticker!r}
          AND date BETWEEN '{start}' AND '{end}'
    """
    df = db.raw_sql(sql, date_cols=["date"])
    df.to_parquet(cache, index=False)
    return df


# ── 경계 검증 ──
def _validate_panel(df: pd.DataFrame, key: str) -> None:
    if df is None or df.empty:
        raise ValueError(f"[{key}] 빈 데이터가 반환되었습니다. 티커/기간/소스를 확인하세요.")
    required = {"date", "ticker", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"[{key}] 필수 컬럼 누락: {missing}")
    if df["close"].isna().all():
        raise ValueError(f"[{key}] close 가 전부 NaN 입니다.")
    # 부분 실패 감지: 일부 종목만 다운로드 실패해 전부 NaN 인 경우를 잡는다.
    # (예: yfinance 캐시 lock 으로 특정 티커만 비는 상황 → silent bad data 방지)
    if "ticker" in df.columns:
        per_ticker_all_nan = df.groupby("ticker")["close"].apply(lambda s: s.isna().all())
        bad = per_ticker_all_nan[per_ticker_all_nan].index.tolist()
        if bad:
            raise ValueError(f"[{key}] 다음 종목의 close 가 전부 NaN 입니다(다운로드 실패 의심): {bad}")
