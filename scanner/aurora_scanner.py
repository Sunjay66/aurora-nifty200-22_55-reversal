import json
import warnings
from datetime import datetime, time
from zoneinfo import ZoneInfo
from io import StringIO

import numpy as np
import pandas as pd
import requests
import yfinance as yf

warnings.filterwarnings("ignore")

IST = ZoneInfo("Asia/Kolkata")

NIFTY200_URL = "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/153.0 Safari/537.36"
    ),
    "Referer": "https://www.niftyindices.com/",
}

EMA_FAST = 22
EMA_SLOW = 55
EMA_LONG_1 = 150
EMA_LONG_2 = 200

CROSS_LOOKBACK = 3
RVOL_LOOKBACK = 20
MACD_LOOKBACK = 20
DATA_PERIOD = "3y"


def now_ist():
    return datetime.now(IST)


def fmt_dt(dt):
    return dt.strftime("%d-%b-%Y %I:%M %p IST")


def clean_float(value):
    if value is None or pd.isna(value):
        return None

    value = float(value)

    if not np.isfinite(value):
        return None

    return round(value, 2)


def get_universe():

    response = requests.get(
        NIFTY200_URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    nifty200 = pd.read_csv(StringIO(response.text))

    symbols = (
        nifty200["Symbol"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .tolist()
    )

    return [symbol + ".NS" for symbol in symbols]


def candle_pattern(df, index):

    if index < 2:
        return "None"

    previous = df.iloc[index - 1]
    current = df.iloc[index]
    first = df.iloc[index - 2]

    po = float(previous["Open"])
    pc = float(previous["Close"])
    ph = float(previous["High"])
    pl = float(previous["Low"])

    co = float(current["Open"])
    cc = float(current["Close"])
    ch = float(current["High"])
    cl = float(current["Low"])

    body = abs(cc - co)

    upper_shadow = ch - max(co, cc)
    lower_shadow = min(co, cc) - cl

    bullish_engulfing = (
        pc < po
        and cc > co
        and co <= pc
        and cc >= po
    )

    hammer = (
        cc > co
        and lower_shadow >= 2 * max(body, 1e-9)
        and upper_shadow <= max(body, 1e-9)
    )

    piercing_line = (
        pc < po
        and cc > co
        and co <= pl
        and cc > (po + pc) / 2
        and cc < po
    )

    first_bearish = pc < po

    middle_body = abs(
        float(first["Close"]) - float(first["Open"])
    )

    middle_range = max(
        float(first["High"]) - float(first["Low"]),
        1e-9
    )

    morning_star = (
        first_bearish
        and middle_body <= 0.35 * middle_range
        and cc > co
        and cc > (po + pc) / 2
    )

    bullish_harami = (
        pc < po
        and cc > co
        and co >= pc
        and cc <= po
    )

    patterns = []

    if bullish_engulfing:
        patterns.append("Bullish Engulfing")

    if hammer:
        patterns.append("Hammer")

    if piercing_line:
        patterns.append("Piercing Line")

    if morning_star:
        patterns.append("Morning Star")

    if bullish_harami:
        patterns.append("Bullish Harami")

    return ", ".join(patterns) if patterns else "None"


def macd_info(df):

    close = df["Close"].astype(float)

    ema12 = close.ewm(
        span=12,
        adjust=False
    ).mean()

    ema26 = close.ewm(
        span=26,
        adjust=False
    ).mean()

    macd = ema12 - ema26

    signal = macd.ewm(
        span=9,
        adjust=False
    ).mean()

    histogram = macd - signal

    latest_index = len(df) - 1

    age = None

    start = max(
        1,
        latest_index - MACD_LOOKBACK + 1
    )

    for index in range(
        latest_index,
        start - 1,
        -1
    ):

        if (
            macd.iloc[index - 1] <= signal.iloc[index - 1]
            and macd.iloc[index] > signal.iloc[index]
        ):

            age = latest_index - index

            break

    if age is None:

        status = "No bullish cross in last 20 sessions"

    else:

        status = (
            f"Bullish Cross — {age} "
            f"session{'s' if age != 1 else ''} ago"
        )

    return (
        clean_float(macd.iloc[-1]),
        clean_float(signal.iloc[-1]),
        clean_float(histogram.iloc[-1]),
        status
    )


def scan_symbol(symbol, df):

    df = df.dropna(
        subset=[
            "Close",
            "Open",
            "High",
            "Low",
            "Volume"
        ]
    ).copy()

    if len(df) < 220:
        return None

    df["EMA22"] = df["Close"].ewm(
        span=22,
        adjust=False
    ).mean()

    df["EMA55"] = df["Close"].ewm(
        span=55,
        adjust=False
    ).mean()

    df["EMA150"] = df["Close"].ewm(
        span=150,
        adjust=False
    ).mean()

    df["EMA200"] = df["Close"].ewm(
        span=200,
        adjust=False
    ).mean()

    latest_index = len(df) - 1

    cross = None

    # IMPORTANT:
    # Only ages 1, 2 and 3 are tested.
    # Current-session age 0 is deliberately excluded.

    for age in (1, 2, 3):

        index = latest_index - age

        if index <= 0:
            continue

        previous = df.iloc[index - 1]
        current = df.iloc[index]

        bullish_cross = (
            previous["EMA22"] <= previous["EMA55"]
            and current["EMA22"] > current["EMA55"]
        )

        if bullish_cross:

            cross = (
                age,
                index
            )

            break

    if cross is None:
        return None

    age, cross_index = cross

    latest = df.iloc[latest_index]

    # Mandatory filters
    if not (
        latest["Close"] > latest["EMA22"]
        and latest["Close"] > latest["EMA55"]
        and latest["Close"] > latest["EMA150"]
        and latest["Close"] > latest["EMA200"]
        and latest["EMA150"] > latest["EMA200"]
    ):
        return None

    # Secondary information only
    average_volume = (
        df["Volume"]
        .shift(1)
        .rolling(RVOL_LOOKBACK)
        .mean()
        .iloc[-1]
    )

    if pd.notna(average_volume) and average_volume:
        rvol = latest["Volume"] / average_volume
    else:
        rvol = None

    macd, macd_signal, macd_histogram, macd_status = (
        macd_info(df)
    )

    cross_date = pd.Timestamp(
        df.index[cross_index]
    ).date()

    return {

        "stock": symbol.replace(".NS", ""),

        "cross_date": cross_date.strftime(
            "%d-%b-%Y"
        ),

        "sessions_since_cross": int(age),

        "cmp": clean_float(
            latest["Close"]
        ),

        "ema22": clean_float(
            latest["EMA22"]
        ),

        "ema55": clean_float(
            latest["EMA55"]
        ),

        "ema150": clean_float(
            latest["EMA150"]
        ),

        "ema200": clean_float(
            latest["EMA200"]
        ),

        "macd": macd,

        "macd_signal": macd_signal,

        "macd_histogram": macd_histogram,

        "macd_status": macd_status,

        "rvol": clean_float(
            rvol
        ),

        "candle": candle_pattern(
            df,
            latest_index
        ),

        "spread_22_55": clean_float(
            latest["EMA22"] - latest["EMA55"]
        ),

        "spread_150_200": clean_float(
            latest["EMA150"] - latest["EMA200"]
        )
    }


def main():

    fetched_at = now_ist()

    print("Downloading Nifty 200 universe...")

    symbols = get_universe()

    print(
        f"Nifty 200 symbols received: {len(symbols)}"
    )

    print("Downloading 3 years of daily data...")

    data = yf.download(
        symbols,
        period=DATA_PERIOD,
        interval="1d",
        auto_adjust=False,
        group_by="ticker",
        threads=True,
        progress=False
    )

    if data is None or data.empty:
        raise RuntimeError(
            "Yahoo Finance returned no market data."
        )

    results = []

    latest_dates = []

    top_level_symbols = set(
        data.columns.get_level_values(0)
    )

    for symbol in symbols:

        try:

            if symbol not in top_level_symbols:
                continue

            df = data[symbol].copy()

            usable = df.dropna(
                subset=["Close"]
            )

            if not usable.empty:

                latest_dates.append(
                    pd.Timestamp(
                        usable.index[-1]
                    ).date()
                )

            result = scan_symbol(
                symbol,
                df
            )

            if result is not None:
                results.append(result)

        except Exception as exc:

            print(
                f"Skipping {symbol}: {exc}"
            )

    if not latest_dates:

        raise RuntimeError(
            "No usable market data was downloaded."
        )

    market_date = max(latest_dates)

    current_date = now_ist().date()

    if market_date == current_date:

        market_status = (
            "CLOSED — TODAY'S DATA"
        )

    else:

        market_status = (
            "CLOSED — LAST TRADING DATA"
        )

    market_session_datetime = datetime.combine(
        market_date,
        time(15, 30),
        tzinfo=IST
    )

    page_refreshed_at = now_ist()

    results.sort(
        key=lambda item: (
            item["sessions_since_cross"],
            item["stock"]
        )
    )

    payload = {

        "scanner_name":
            "Aurora Nifty 200 — Daily 22/55 Trend Reversal",

        "generated_at":
            page_refreshed_at.isoformat(),

        "market_status":
            market_status,

        "market_data_date":
            market_date.isoformat(),

        "market_data_session_display":
            fmt_dt(
                market_session_datetime
            ),

        "data_fetched_at":
            fetched_at.isoformat(),

        "data_fetched_display":
            fmt_dt(
                fetched_at
            ),

        "page_refreshed_at":
            page_refreshed_at.isoformat(),

        "page_refreshed_display":
            fmt_dt(
                page_refreshed_at
            ),

        "universe":
            "Nifty 200",

        "timeframe":
            "Daily",

        "candidate_count":
            len(results),

        "mandatory_rules": [

            "22 EMA crossed above 55 EMA within 1–3 completed sessions.",

            "Current price above 22, 55, 150 and 200 EMA.",

            "150 EMA above 200 EMA."
        ],

        "secondary_note":
            "MACD, RVOL and reversal candles are displayed as secondary information only and do not filter candidates.",

        "candidates":
            results
    }

    with open(
        "data/latest_results.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            payload,
            file,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 60)
    print("AURORA NIFTY 200 SCANNER")
    print("=" * 60)
    print(
        f"Universe: {len(symbols)}"
    )
    print(
        f"Market data session: {market_date}"
    )
    print(
        f"Candidates: {len(results)}"
    )

    for result in results:

        print(
            result["stock"],
            "|",
            f"cross age={result['sessions_since_cross']}",
            "|",
            f"CMP={result['cmp']}"
        )

    print("=" * 60)


if __name__ == "__main__":
    main()
