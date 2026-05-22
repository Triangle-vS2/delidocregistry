import requests
import json
import os
import pandas as pd
#   Set credentials as environment variables
#   API key = at14cef94iykyk217u
API_KEY = os.getenv("APCA_API_KEY_ID", "PKBCF961I2T0C5GJD2BX")
SECRET_KEY = os.getenv("APCA_API_SECRET_KEY", "aW8JY1ZnacveKistGq71KYVhSNTEz6o55tBthRHx")
#   Set Base Urls and Header parameters
#   Look for the api key in the main program delivery app
PAPER_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"  # Correct endpoint for historical market data
ACCOUNT_URL = f"{PAPER_URL}/v2/account"
ORDERS_URL = f"{PAPER_URL}/v2/orders"
HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY
}
#   Est account
def get_account():
    r = requests.get(ACCOUNT_URL, headers=HEADERS)
    r.raise_for_status()
    return r.json()
#   Test recent orders
def create_order(symbol, qty, side, type, time_in_force):
    data = {
        'symbol': symbol,
        'qty': qty,
        'side': side,
        'type': type,
        'time_in_force': time_in_force 
    }
    r = requests.post(ORDERS_URL, json=data, headers=HEADERS)
    r.raise_for_status()
    return r.json()
def get_orders():
    r = requests.get(ORDERS_URL, headers=HEADERS)
    r.raise_for_status()
    return r.json()
#   Gather some recent data
def get_historical_data(symbol, start, end, limit, timeframe):
    url = f"{DATA_URL}/v2/stocks/{symbol}/bars"
    params = {
        "start": start,
        "end": end,
        "limit": limit,
        "timeframe": timeframe
    }
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    data = r.json()
    return data.get("bars", [])
def read_file():
    with open("results", "r") as f:
        lines = f.readlines()
    prices = [float(line.strip()) for line in lines]
    return prices
def save_symbol_csv(symbol, start, end, folder="data"):
    """Fetch symbol data and save to CSV."""
    os.makedirs(folder, exist_ok=True)  # create folder if it doesn't exist
    bars = get_historical_data(symbol, start, end, 1000, "1D")
    if not bars:
        print(f"No data for {symbol}")
        return
    df = pd.DataFrame(bars)
    df['t'] = pd.to_datetime(df['t'])
    df.rename(columns={'t': 'date'}, inplace=True)
    filename = os.path.join(folder, f"{symbol}.csv")
    df.to_csv(filename, index=False)
    print(f"Saved {filename} with {len(df)} rows")
def create_csvs_for_symbols(symbols):
    for sym in symbols:
        save_symbol_csv(sym,
                        start="2023-01-01T00:00:00Z",
                        end="2023-12-31T00:00:00Z")
#   Use three Strategys
def mean_reversion_strategy(prices, window=20, threshold=0.02):
    signals = pd.Series(0, index=prices.index)
    moving_avg = prices.rolling(window=window).mean()
    for i in range(len(prices)):
        if prices.iloc[i] < moving_avg.iloc[i] * (1 - threshold):
            signals.iloc[i] = 1  # Buy signal - price below lower threshold
        elif prices.iloc[i] > moving_avg.iloc[i] * (1 + threshold):
            signals.iloc[i] = -1  # Sell signal - price above upper threshold
        else:
            signals.iloc[i] = 0   # Hold
    return signals
def momentum_strategy(prices, lookback=10):
    signals = pd.Series(0, index=prices.index)
    for i in range(lookback, len(prices)):
        momentum = prices.iloc[i] - prices.iloc[i - lookback]
        if momentum > 0:
            signals.iloc[i] = 1   # Buy signal - positive momentum
        elif momentum < 0:
            signals.iloc[i] = -1  # Sell signal - negative momentum
        else:
            signals.iloc[i] = 0   # Hold
    return signals
def sma_cs(prices):
    position = 0
    buy = 0
    tot_profit = 0
    for i in range(5, len(prices)):
        avg = sum(prices[i-5:i]) / 5
        price = prices[i]
        if price > avg and position != 1:
            buy = price
            position = 1
            print(f"Buying at: {price}")
        elif price < avg and position == 1:
            sell = price
            profit = sell - buy
            tot_profit += profit
            position = 0
            print(f"Selling at: {sell}, Profit: {profit}")
    return tot_profit
def compare_all_strategies_for_all_symbols(symbol_list):
    results = {}
    for sym in symbol_list:
        try:
            df = pd.read_csv(f"data/{sym}.csv")  # Assuming CSVs are stored in data folder
        except FileNotFoundError:
            print(f"CSV for {sym} not found, skipping.")
            continue
        prices = df['c'].tolist()
        pseries = pd.Series(prices)
    # SMA crossover results
        profit_sma = sma_cs(prices)
#   Mean Reversion results
        signals_meanrev = mean_reversion_strategy(pseries).tolist()
        profit_meanrev = compute_strategy_profit(prices, signals_meanrev)
#   Momentum results
        signals_momentum = momentum_strategy(pseries).tolist()
        profit_momentum = compute_strategy_profit(prices, signals_momentum)
        results[sym] = {
            'SMA Cross': profit_sma,
            'Mean Reversion': profit_meanrev,
            'Momentum': profit_momentum
        }
        print(f"{sym}: SMA: {profit_sma:.2f}, MeanRev: {profit_meanrev:.2f}, Momentum: {profit_momentum:.2f}")
#   Identify top performing stock Symbol
    top_stock, top_strategy, top_profit = None, None, float('-inf')
    for stock, strat_profits in results.items():
        for strat, profit in strat_profits.items():
            if profit > top_profit:
                top_stock, top_strategy, top_profit = stock, strat, profit
    summary = {
        'results': results,
        'top_performer': {
            'Stock': top_stock,
            'Strategy': top_strategy,
            'Profit': top_profit
        }
    }
    with open('results.json', 'w') as f:
        json.dump(summary, f, indent=4)
    print(f"\nTop performer: {top_stock} with strategy {top_strategy}, profit: {top_profit:.2f}")
def compute_strategy_profit(prices, signals):
    position = 0        # 0 = no position, 1 = long, -1 = short
    entry_price = 0.0
    profit = 0.0
    for i in range(len(signals)):
        signal = signals[i]
        price = prices[i]
        if signal == 1 and position <= 0:       # go long or close short
            if position == -1:  # close short
                profit += entry_price - price
            entry_price = price
            position = 1
        elif signal == -1 and position >= 0:    # go short or close long
            if position == 1:  # close long
                profit += price - entry_price
            entry_price = price
            position = -1
#   Close open position to finish
    if position == 1:
        profit += prices[-1] - entry_price
    elif position == -1:
        profit += entry_price - prices[-1]
    return profit
def main():
    symbol_list = ['MSFT', 'AAPL', 'JNJ', 'KO', 'VOO', 'WGO', 'DAL', 'F', 'BAC', 'CRON']
#   create CSVs 
    create_csvs_for_symbols(symbol_list)
    compare_all_strategies_for_all_symbols(symbol_list)
if __name__ == "__main__":
    main()