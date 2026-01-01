"""간단한 KODEX ETF 12월 상승률 및 다음날 수익률 분석 스크립트.

Daum 금융의 차트 API를 활용해 후보 ETF 중 12월 월간 수익률이 가장 높은
종목을 선정하고, 해당 종목의 '종가 매수 -> 다음 거래일 종가 매도' 수익률을
요약합니다.

표준 라이브러리만 사용하도록 작성해 네트워크만 통한다면 별도 패키지 설치 없이
즉시 실행할 수 있습니다.
"""
from __future__ import annotations

import datetime as _dt
import json
import math
import statistics
from dataclasses import dataclass
from typing import Iterable, List
from urllib import error, request


@dataclass
class Candle:
    date: _dt.date
    close: float


def _parse_date(date_str: str) -> _dt.date:
    return _dt.datetime.strptime(date_str, "%Y-%m-%d").date()


def fetch_daum_daily(code_6: str, limit: int = 400) -> List[Candle]:
    """다음 금융 일봉 데이터 조회.

    Args:
        code_6: 6자리 종목 코드 (예: "395160")
        limit: 조회할 캔들 수

    Returns:
        Candle 리스트 (오름차순)
    """

    url = f"https://finance.daum.net/api/charts/A{code_6}/days?limit={limit}&adjusted=true"
    headers = {
        "referer": "https://finance.daum.net/chart/A005930",
        "user-agent": "Mozilla/5.0",
    }
    req = request.Request(url, headers=headers, method="GET")

    try:
        with request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:  # pragma: no cover - 네트워크 의존
        print(f"HTTPError {exc.code} for code {code_6}: {exc.reason}")
        return []
    except error.URLError as exc:  # pragma: no cover - 네트워크 의존
        print(f"URLError for code {code_6}: {exc.reason}")
        return []

    rows = data.get("data", []) or []
    candles: List[Candle] = []
    for row in rows:
        try:
            date = _parse_date(str(row["date"]))
            close = float(row["tradePrice"])
        except (KeyError, TypeError, ValueError):
            continue
        candles.append(Candle(date=date, close=close))

    candles.sort(key=lambda c: c.date)
    return candles


def _filter_period(candles: Iterable[Candle], start: _dt.date, end: _dt.date) -> List[Candle]:
    return [c for c in candles if start <= c.date <= end]


def analyze_nextday_returns(candles: List[Candle], start: str, end: str) -> List[dict]:
    """기간 내 '종가 매수 -> 다음 거래일 종가 매도' 수익률 계산."""

    start_dt = _parse_date(start)
    end_dt = _parse_date(end)
    base = _filter_period(candles, start_dt, end_dt)

    results: List[dict] = []
    for today, tomorrow in zip(base, base[1:]):
        ret_nextday = (tomorrow.close / today.close) - 1.0
        results.append(
            {
                "date": today.date,
                "close": today.close,
                "next_date": tomorrow.date,
                "next_close": tomorrow.close,
                "ret_nextday": ret_nextday,
            }
        )
    return results


def summarize(ret_rows: List[dict]) -> dict:
    """수익률 요약 통계."""

    if not ret_rows:
        return {
            "표본수(n)": 0,
            "평균(%)": math.nan,
            "중앙값(%)": math.nan,
            "승률(%)": math.nan,
            "최대(%)": math.nan,
            "최소(%)": math.nan,
            "표준편차(%)": math.nan,
        }

    r = [row["ret_nextday"] for row in ret_rows]
    win_ratio = sum(1 for x in r if x > 0) / len(r) * 100
    std_pct = statistics.stdev(r) * 100 if len(r) > 1 else 0.0
    return {
        "표본수(n)": len(r),
        "평균(%)": statistics.mean(r) * 100,
        "중앙값(%)": statistics.median(r) * 100,
        "승률(%)": win_ratio,
        "최대(%)": max(r) * 100,
        "최소(%)": min(r) * 100,
        "표준편차(%)": std_pct,
    }


def _format_percent(value: float) -> str:
    if math.isnan(value):
        return "nan"
    return f"{value:.4f}"


def main():
    candidates = {
        "069500": "KODEX 200",
        "395160": "KODEX AI반도체",
        "305720": "KODEX 2차전지산업",
        "091160": "KODEX 반도체",
        "122630": "KODEX 레버리지",
        "114800": "KODEX 인버스",
    }

    start = "2025-12-01"
    end = "2025-12-31"

    rank_rows = []
    for code, name in candidates.items():
        candles = fetch_daum_daily(code, limit=450)
        if not candles:
            continue

        dec = _filter_period(candles, _parse_date(start), _parse_date(end))
        if len(dec) < 2:
            continue

        month_ret = dec[-1].close / dec[0].close - 1.0
        rank_rows.append(
            {
                "code": code,
                "name": name,
                "dec_return": month_ret,
                "dec_first_close": dec[0].close,
                "dec_last_close": dec[-1].close,
            }
        )

    rank_rows.sort(key=lambda row: row["dec_return"], reverse=True)

    print("\n[12월 상승 강도 TOP (후보군 내)]")
    if not rank_rows:
        print("후보군에서 12월 데이터 확보 실패. CANDIDATES 코드 확인 필요.")
        return

    for row in rank_rows[:10]:
        print(
            f"{row['code']} {row['name']}: {row['dec_return']*100:.4f}% "
            f"({row['dec_first_close']:.2f} -> {row['dec_last_close']:.2f})"
        )

    top = rank_rows[0]
    top_code = top["code"]
    top_name = top["name"]

    candles_top = fetch_daum_daily(top_code, limit=450)
    ret_rows = analyze_nextday_returns(candles_top, start, end)
    stats = summarize(ret_rows)

    print(f"\n[선정 종목] {top_name} ({top_code})")
    print("[12월 '종가 매수 -> 다음 거래일 종가' 수익률 요약]")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"- {key}: {_format_percent(value)}")
        else:
            print(f"- {key}: {value}")

    print("\n[베스트 5] 다음날 수익률 상위")
    best_rows = sorted(ret_rows, key=lambda r: r["ret_nextday"], reverse=True)[:5]
    for row in best_rows:
        print(
            f"{row['date']} -> {row['next_date']}: {row['ret_nextday']*100:.4f}% "
            f"({row['close']:.2f} -> {row['next_close']:.2f})"
        )

    print("\n[워스트 5] 다음날 수익률 하위")
    worst_rows = sorted(ret_rows, key=lambda r: r["ret_nextday"])[:5]
    for row in worst_rows:
        print(
            f"{row['date']} -> {row['next_date']}: {row['ret_nextday']*100:.4f}% "
            f"({row['close']:.2f} -> {row['next_close']:.2f})"
        )

    equity = 1.0
    print("\n[12월 누적(재투입 가정) 최종 배수]")
    for row in ret_rows[-5:]:
        equity *= 1 + row["ret_nextday"]
        print(f"{row['date']} -> {row['next_date']}: equity {equity:.4f}")


if __name__ == "__main__":
    main()
