import streamlit as st
import yfinance as yf
import pandas as pd
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Tuple, List

# 페이지 제목
st.title("\U0001F4CA 글로벌 금융 대시보드")
st.write("실시간으로 원자재, 주요 지수 및 환율을 확인할 수 있는 대시보드입니다.")

# ------------------ 데이터 가져오기 ------------------

# 1. 원자재 데이터
commodities = {
    "금": "GC=F",
    "원유": "CL=F",
    "천연가스": "NG=F",
    "은": "SI=F",
    "구리": "HG=F",
    "백금": "PL=F",
    "옥수수": "ZC=F",
    "대두": "ZS=F",
    "밀": "ZW=F"
}

# 2. 글로벌 주요 지수 데이터 (현물 및 선물 구분)
indices_spot = {
    "나스닥 (현물)": "^IXIC",
    "다우존스 (현물)": "^DJI",
    "S&P 500 (현물)": "^GSPC",
    "니케이 225 (현물)": "^N225",
    "FTSE 100 (영국)": "^FTSE",
    "DAX (독일)": "^GDAXI",
    "상해 종합 (중국)": "000001.SS",
    "코스피 (한국)": "^KS11",
    "코스닥 (한국)": "^KQ11"
}

indices_futures = {
    "나스닥 (선물)": "NQ=F",
    "다우존스 (선물)": "YM=F",
    "S&P 500 (선물)": "ES=F",
}

# 3. 주요 환율 데이터 (USD 기준)
forex_pairs = {
    "달러/유로": "EURUSD=X",
    "달러/엔": "JPY=X",
    "달러/파운드": "GBPUSD=X",
    "달러/위안": "CNY=X",
    "달러/원": "KRW=X"
}

# 4. 미국 국채 데이터
us_bonds = {
    "미국 단기 국채 (1년물)": "^IRX",
    "미국 중기 국채 (5년물)": "^FVX",
    "미국 장기 국채 (10년물)": "^TNX",
    "미국 초장기 국채 (30년물)": "^TYX"
}

# 5. 코인 데이터
crypto = {
    "비트코인": "BTC-USD",
    "이더리움": "ETH-USD",
    "리플": "XRP-USD",
    "솔라나": "SOL-USD",
    "바이낸스코인": "BNB-USD",
    "도지코인": "DOGE-USD",
    "에이다": "ADA-USD",
    "트론": "TRX-USD",
    "아발란체": "AVAX-USD"
}

# ------------------ 함수 정의 ------------------

# 전일 종가 캐싱
prev_close_cache = {}

async def fetch_single_price(ticker: str, timeout: int = 10) -> Tuple[float, float]:
    """단일 자산 데이터를 가져오는 비동기 함수 (타임아웃 추가)"""
    try:
        async def fetch_data():
            ticker_data = yf.Ticker(ticker)
            history = ticker_data.history(period="1d")
            if ticker not in prev_close_cache:
                prev_close_cache[ticker] = ticker_data.info.get("previousClose", None)
            prev_close = prev_close_cache[ticker]
            if not history.empty:
                current_price = history["Close"].iloc[-1]
                change_percent = (
                    round(((current_price - prev_close) / prev_close) * 100, 2)
                    if prev_close
                    else None
                )
                return current_price, change_percent
            else:
                return None, None

        # 타임아웃 설정
        return await asyncio.wait_for(fetch_data(), timeout=timeout)
    except asyncio.TimeoutError:
        print(f"Timeout fetching data for {ticker}")
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
    return None, None

async def fetch_all_prices(assets: Dict[str, str], batch_size: int = 5) -> List[Tuple[float, float]]:
    """여러 자산 데이터를 비동기로 가져오는 함수 (배치 처리 추가)"""
    tickers = list(assets.values())
    results = []

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i + batch_size]
        tasks = [fetch_single_price(ticker) for ticker in batch]
        results.extend(await asyncio.gather(*tasks))
    
    return results

def create_dataframe(data, asset_names):
    """데이터를 DataFrame 형태로 변환"""
    formatted_data = [
        {
            "자산": name,
            "현재 가격 (USD)": f"<span style='color:red; text-align:right; padding-right:10px;'>{price:.2f}</span>" if change and change > 0 else f"<span style='color:#4682B4; text-align:right; padding-right:10px;'>{price:.2f}</span>" if change and change < 0 else f"<span style='text-align:right; padding-right:10px;'>{price:.2f}</span>" if price is not None else "데이터 없음",
            "등락률 (%)": f"<span style='color:red; text-align:right; padding-right:10px;'>{change:.2f}%</span>" if change and change > 0 else f"<span style='color:#4682B4; text-align:right; padding-right:10px;'>{change:.2f}%</span>" if change and change < 0 else "데이터 없음",
        }
        for name, (price, change) in zip(asset_names, data)
    ]
    df = pd.DataFrame(formatted_data)
    return df.to_html(escape=False, index=False, classes='styled-table')

def create_crypto_dataframe(data, asset_names):
    """코인 데이터를 DataFrame 형태로 변환 (현재 가격은 소수점 4째 자리까지)"""
    formatted_data = [
        {
            "자산": name,
            "현재 가격 (USD)": f"<span style='color:red; text-align:right; padding-right:10px;'>{price:.4f}</span>" if change and change > 0 else f"<span style='color:#4682B4; text-align:right; padding-right:10px;'>{price:.4f}</span>" if change and change < 0 else f"<span style='text-align:right; padding-right:10px;'>{price:.4f}</span>" if price is not None else "데이터 없음",
            "등락률 (%)": f"<span style='color:red; text-align:right; padding-right:10px;'>{change:.2f}%</span>" if change and change > 0 else f"<span style='color:#4682B4; text-align:right; padding-right:10px;'>{change:.2f}%</span>" if change and change < 0 else "데이터 없음",
        }
        for name, (price, change) in zip(asset_names, data)
    ]
    df = pd.DataFrame(formatted_data)
    return df.to_html(escape=False, index=False, classes='styled-table')

def add_custom_css():
    """CSS 추가"""
    st.markdown(
        """
        <style>
        .styled-table th {
            text-align: center;
        }
        .styled-table td {
            text-align: right;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# ------------------ 대시보드 표시 ------------------

# 초기 표 설정
placeholders = {
    "commodities": st.empty(),
    "indices_spot": st.empty(),
    "indices_futures": st.empty(),
    "forex": st.empty(),
    "bonds": st.empty(),
    "crypto": st.empty(),
    "update_time": st.empty()
}

def render_initial_tables():
    # 원자재 데이터
    placeholders["commodities_title"] = st.container()
    with placeholders["commodities_title"]:
        st.markdown("## \U0001F4B0 원자재")
    placeholders["commodities_table"] = st.empty()
    placeholders["commodities_table"].markdown(create_dataframe([(None, None)] * len(commodities), commodities.keys()), unsafe_allow_html=True)

    # 주요 지수 (현물)
    placeholders["indices_spot_title"] = st.container()
    with placeholders["indices_spot_title"]:
        st.markdown("## \U0001F4C8 주요 지수 (현물)")
    placeholders["indices_spot_table"] = st.empty()
    placeholders["indices_spot_table"].markdown(create_dataframe([(None, None)] * len(indices_spot), indices_spot.keys()), unsafe_allow_html=True)

    # 주요 지수 (선물)
    placeholders["indices_futures_title"] = st.container()
    with placeholders["indices_futures_title"]:
        st.markdown("## \U0001F4C9 주요 지수 (선물)")
    placeholders["indices_futures_table"] = st.empty()
    placeholders["indices_futures_table"].markdown(create_dataframe([(None, None)] * len(indices_futures), indices_futures.keys()), unsafe_allow_html=True)

    # 주요 환율
    placeholders["forex_title"] = st.container()
    with placeholders["forex_title"]:
        st.markdown("## \U0001F4B1 주요 환율")
    placeholders["forex_table"] = st.empty()
    placeholders["forex_table"].markdown(create_dataframe([(None, None)] * len(forex_pairs), forex_pairs.keys()), unsafe_allow_html=True)

    # 미국 국채
    placeholders["bonds_title"] = st.container()
    with placeholders["bonds_title"]:
        st.markdown("## \U0001F4B5 미국 국채")
    placeholders["bonds_table"] = st.empty()
    placeholders["bonds_table"].markdown(create_dataframe([(None, None)] * len(us_bonds), us_bonds.keys()), unsafe_allow_html=True)

    # 주요 코인
    placeholders["crypto_title"] = st.container()
    with placeholders["crypto_title"]:
        st.markdown("## \U0001FA99 주요 코인")
    placeholders["crypto_table"] = st.empty()
    placeholders["crypto_table"].markdown(create_crypto_dataframe([(None, None)] * len(crypto), crypto.keys()), unsafe_allow_html=True)

    # 데이터 갱신 시간
    placeholders["update_time"] = st.empty()
    placeholders["update_time"].markdown("**데이터 갱신 시각:** 데이터 로딩 중...")



async def update_dashboard():
    """데이터를 주기적으로 업데이트하는 함수"""
    while True:
        # 데이터 갱신
        commodity_prices = await fetch_all_prices(commodities)
        indices_spot_prices = await fetch_all_prices(indices_spot)
        indices_futures_prices = await fetch_all_prices(indices_futures)
        forex_rates = await fetch_all_prices(forex_pairs)
        bond_prices = await fetch_all_prices(us_bonds)
        crypto_prices = await fetch_all_prices(crypto)

        # 표 갱신
        placeholders["commodities_table"].markdown(
            create_dataframe(commodity_prices, commodities.keys()), unsafe_allow_html=True
        )
        placeholders["indices_spot_table"].markdown(
            create_dataframe(indices_spot_prices, indices_spot.keys()), unsafe_allow_html=True
        )
        placeholders["indices_futures_table"].markdown(
            create_dataframe(indices_futures_prices, indices_futures.keys()), unsafe_allow_html=True
        )
        placeholders["forex_table"].markdown(
            create_dataframe(forex_rates, forex_pairs.keys()), unsafe_allow_html=True
        )
        placeholders["bonds_table"].markdown(
            create_dataframe(bond_prices, us_bonds.keys()), unsafe_allow_html=True
        )
        placeholders["crypto_table"].markdown(
            create_crypto_dataframe(crypto_prices, crypto.keys()), unsafe_allow_html=True
        )

        # 한국 시간으로 갱신 시간 표시
        current_time_kst = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
        placeholders["update_time"].markdown(f"**데이터 갱신 시각:** {current_time_kst}")


        # 5초 간격 갱신
        await asyncio.sleep(10)

# Streamlit에서 비동기 루프 실행
def main():
    asyncio.run(update_dashboard())

if __name__ == "__main__":
    add_custom_css()
    render_initial_tables()
    main()
