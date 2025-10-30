import ccxt
import pandas as pd
import time
from datetime import datetime
import requests

# 🔔 Telegram Setup - REPLACE THESE VALUES!
TELEGRAM_BOT_TOKEN = '7842209631:AAGs8BbVmUrpaA7nlGpq9IqXKqQvOM9Dr1Q'  # <- Enter your real token here
TELEGRAM_CHAT_ID = '1771875777'      # <- Enter your real chat ID here

class RsiDivergenceScanner:
    def __init__(self):
        # Binance setup
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        # Get ALL spot symbols
        markets = self.exchange.load_markets()
        
        # Filter for USDT pairs, excluding leveraged tokens
        all_usdt_symbols = [symbol for symbol in markets.keys() 
                           if symbol.endswith('/USDT') and 
                              not any(x in symbol for x in ['UP', 'DOWN', 'BULL', 'BEAR'])]
        
        # Define top 20 symbols by market cap (static list based on common large caps)
        # You can update this list periodically if needed
        top_20_symbols = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT',
            'SOL/USDT', 'DOGE/USDT', 'TRX/USDT', 'TON/USDT', 'AVAX/USDT',
            'SHIB/USDT', 'DOT/USDT', 'MATIC/USDT', 'LTC/USDT', 'BCH/USDT',
            'LINK/USDT', 'LEO/USDT', 'FET/USDT', 'UNI/USDT', 'ETC/USDT'
        ]
        
        # Filter to ensure only symbols available on the exchange are included
        self.symbols = [symbol for symbol in top_20_symbols if symbol in all_usdt_symbols]
        print(f"📊 Loaded {len(self.symbols)} symbols to scan (Top 20 USDT Pairs)")
        print(f"   Symbols: {self.symbols}")
    
    def calculate_rsi(self, closes, period=14):
        """Calculate RSI manually"""
        if len(closes) < period + 1:
            # Return a list of None values if not enough data for even one RSI calculation
            return [None] * len(closes)

        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [max(0, delta) for delta in deltas]
        losses = [max(0, -delta) for delta in deltas]
        
        # Initialize RSI list with None for the first 'period' values
        rsis = [None] * period
        
        # Calculate the first RSI value after the initial period
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        if avg_loss != 0:
            initial_rsi = 100 - (100 / (1 + avg_gain / avg_loss))
        else:
            initial_rsi = 100 # If avg_loss is 0, RSI is 100
        rsis.append(initial_rsi)
        
        # Calculate subsequent RSI values
        for i in range(period + 1, len(deltas)):
            # Update average gain and loss using Wilder's smoothing
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss != 0:
                rsi = 100 - (100 / (1 + avg_gain / avg_loss))
            else:
                rsi = 100 # If avg_loss becomes 0, RSI is 100
            rsis.append(rsi)
        
        # The RSI list might still be shorter than the closes list if len(closes) == period + 1 initially
        # The list comprehension for deltas inherently makes it len(closes) - 1
        # Our RSI calculation adds one value after the initial period, making it len(closes) - period values after the initial Nones
        # Total length of rsis should be len(closes) - 1
        # To match the DataFrame length (which is len(closes)), we prepend one more None.
        # Actually, the initial list already has 'period' Nones, and we append (len(deltas) - period) RSI values.
        # len(rsis) = period + (len(deltas) - period) = len(deltas) = len(closes) - 1
        # So, we need to prepend one more None to match the original closes length.
        # The correct approach is to start the rsis list with (period - 1) Nones, then calculate the first RSI after 'period' changes.
        # Let's re-align:
        # Deltas: [1-0, 2-1, ..., N-(N-1)] -> len = N-1
        # RSI needs to start calculating after 'period' deltas are available to get the initial average.
        # So, the first 'period - 1' RSI values are None.
        # The 'period-th' RSI value is calculated from the first 'period' deltas.
        # The resulting RSI list should have length len(closes) - 1.
        # To align with the original DataFrame (length len(closes)), we need to prepend one more None at the start.
        # Let's correct the initial setup:
        # deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))] -> len = len(closes) - 1
        # Initial RSI list: [None] * (period - 1) -> len = period - 1
        # Calculate first RSI using first 'period' deltas -> append -> len = period - 1 + 1 = period
        # Calculate subsequent RSI values using remaining deltas -> len = period + (len(deltas) - period) = len(deltas)
        # So, rsis = [None] * (period - 1) + [calculated_rsis] -> total len = (period - 1) + (len(deltas) - period + 1) wait.
        # deltas len = len(closes) - 1
        # Initial Nones = period - 1
        # Calculated RSI values = len(deltas) - (period - 1) = (len(closes) - 1) - period + 1 = len(closes) - period
        # Total RSI list len = (period - 1) + (len(closes) - period) = len(closes) - 1
        # The DataFrame has len(closes) rows.
        # We need to prepend one more None to make the RSI list length match the DataFrame.
        # Let's adjust the calculation logic slightly to ensure the final list matches the DataFrame length.
        # The standard approach is that RSI[0] to RSI[period-2] are None, RSI[period-1] is the first calculated value.
        # This results in len(RSI) = len(closes), which is correct.
        # The error suggests the RSI list was 49 when df was 50.
        # If we fetch 50 candles, closes = 50.
        # Deltas = 49.
        # Initial Nones = 14 - 1 = 13.
        # Calculated RSI = 49 - 13 = 36.
        # Total RSI list = 13 + 36 = 49. -> This is the problem!
        # The standard RSI calculation has:
        # RSI[0] ... RSI[period-2] = None (so 14 Nones for period=14)
        # RSI[period-1] ... RSI[len(closes)-1] = Calculated values
        # So initial Nones should be 'period', not 'period - 1'.
        # Corrected logic:
        # deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))] -> len = len(closes) - 1
        # Initial RSI list: [None] * period -> len = period
        # Calculate first RSI using first 'period' deltas -> RSI[period] = calc(...)
        # Calculate subsequent RSI values using remaining deltas -> RSI[period+1] ... RSI[len(closes)-1]
        # Number of calculated RSI values = len(closes) - 1 - period = len(deltas) - period
        # Total RSI list len = period + (len(closes) - 1 - period) = len(closes) - 1. -> Still 49 if len(closes)=50!
        # Ah! The first RSI value is calculated *after* observing the 'period'-th price change.
        # So, the RSI value corresponds to the *current* bar, not the *previous* bar after 'period' changes.
        # The RSI list should indeed be len(closes) long.
        # The calculation starts *after* period changes have occurred, meaning the RSI for the *next* bar incorporates those changes.
        # The standard RSI(14) on a list of 50 prices produces 50 RSI values: 14 Nones + 36 calculated.
        # Let's recount:
        # closes = [c0, c1, c2, ..., c49] -> len = 50
        # deltas = [d1, d2, ..., d49] where di = ci - c(i-1) -> len = 49
        # Initial RSI list = [None, None, ..., None] (14 Nones) -> index 0 to 13 -> len = 14
        # Calculate RSI[14] using deltas[0] to deltas[13] (first 14 deltas)
        # Calculate RSI[15] using updated avg gain/loss including deltas[14]
        # ...
        # Calculate RSI[49] using updated avg gain/loss including deltas[49]
        # Total RSI list = [None x14, RSI_val_14, RSI_val_15, ..., RSI_val_49] -> len = 14 + (49 - 14 + 1) = 14 + 36 = 50. -> This is correct!
        # So the initial list should be [None] * period.
        # The first calculation happens for index 'period'.
        # The loop should iterate from 'period' to len(deltas), which is len(closes) - 1.
        # So the RSI list needs to start with 'period' Nones.
        # The number of calculated RSI values is len(deltas) - period + 1 = (len(closes) - 1) - period + 1 = len(closes) - period.
        # Total length = period + (len(closes) - period) = len(closes). -> Perfect!
        # Let's implement the standard RSI calculation correctly:
        if len(closes) < period + 1:
            # Need at least 'period + 1' closes to calculate the first RSI value
            # Return a list of None values matching the closes length
            return [None] * len(closes)

        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))] # len = len(closes) - 1
        gains = [max(0, delta) for delta in deltas]
        losses = [max(0, -delta) for delta in deltas]

        # Initialize RSI list with 'period' Nones
        rsis = [None] * period # This covers indices 0 to period-1

        # Calculate the first RSI value (at index 'period') using the first 'period' gains/losses
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        if avg_loss != 0:
            initial_rsi = 100 - (100 / (1 + avg_gain / avg_loss))
        else:
            initial_rsi = 100
        rsis.append(initial_rsi) # This adds the value at index 'period'

        # Calculate subsequent RSI values
        # Loop from index 'period + 1' up to len(closes) - 1
        # This corresponds to deltas[period] up to deltas[len(deltas)-1]
        for i in range(period, len(deltas)): # i goes from 'period' to len(deltas)-1
            # Update average gain and loss using Wilder's smoothing
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss != 0:
                rsi = 100 - (100 / (1 + avg_gain / avg_loss))
            else:
                rsi = 100
            rsis.append(rsi) # This adds values at indices period+1, period+2, ..., len(closes)-1

        # The length of rsis should now be len(closes)
        assert len(rsis) == len(closes), f"RSI list length {len(rsis)} does not match closes length {len(closes)}"
        return rsis


    def find_swings(self, series):
        """Find swing lows in a series"""
        swings = []
        # Iterate from index 1 to len-2 to check neighbors
        for i in range(1, len(series) - 1):
            val = series[i]
            prev_val = series[i - 1]
            next_val = series[i + 1]

            # Check if the current value is not None and is a local low
            if val is not None and prev_val is not None and next_val is not None:
                if val < prev_val and val < next_val:
                    swings.append((i, val))
        return swings


    def detect_divergence(self, df):
        """Detect RSI bullish divergence on 1m timeframe"""
        closes = df['close'].tolist()
        rsi_values = self.calculate_rsi(closes) # This should now return a list of the same length as closes/df

        # Align RSI with prices by assigning the list to the DataFrame column
        # This should now work as the lengths match
        df['rsi'] = rsi_values

        # Find swing lows in price and RSI
        price_lows = self.find_swings(df['low'].tolist())
        rsi_lows = self.find_swings(rsi_values) # Use the calculated RSI list

        # Check for divergence: price lower low, RSI higher low
        for i in range(len(rsi_lows)):
            for j in range(i + 1, len(rsi_lows)):
                idx2, rsi2 = rsi_lows[j] # Second (later) low
                idx1, rsi1 = rsi_lows[i] # First (earlier) low

                # Distance check (5-25 bars for 1m = 5-25 minutes)
                dist = idx2 - idx1
                if dist < 5 or dist > 25:
                    continue

                # First RSI < 30
                if rsi1 >= 30:
                    continue

                # Find corresponding price lows using the same indices
                try:
                    # Find the price low that corresponds to the first RSI low index
                    _, price1 = next((k, low) for k, low in price_lows if k == idx1)
                    # Find the price low that corresponds to the second RSI low index
                    _, price2 = next((k, low) for k, low in price_lows if k == idx2)
                except StopIteration:
                    # If no corresponding price low found at the exact RSI low index, skip
                    # This can happen if an RSI low occurs at an index where the price is not a swing low
                    continue

                # Check for bullish divergence: price makes lower low, RSI makes higher low
                if price2 < price1 and rsi2 > rsi1:
                    return {
                        'symbol': df['symbol'].iloc[0],
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), # More precise time
                        'tf': df['timeframe'].iloc[0], # Added timeframe for clarity
                        'rsi1': round(rsi1, 2),
                        'rsi2': round(rsi2, 2),
                        'price1': round(price1, 6),
                        'price2': round(price2, 6),
                        'distance': dist
                    }
        return None


    def send_notification(self, divergence):
        """Send Telegram notification"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️  No Telegram token or chat ID provided. Skipping notification.")
            return
            
        message = f"""
🔍 <b>RSI Divergence Alert!</b>

📊 <b>Symbol:</b> {divergence['symbol']}
⏱️ <b>Timeframe:</b> {divergence['tf']}
⏰ <b>Detection Time:</b> {divergence['time']}
📉 <b>First RSI:</b> {divergence['rsi1']} (oversold!)
📈 <b>Second RSI:</b> {divergence['rsi2']}
💰 <b>Price 1:</b> {divergence['price1']}
💰 <b>Price 2:</b> {divergence['price2']}
📏 <b>Distance:</b> {divergence['distance']} bars ({divergence['distance']} min)

✅ Bullish RSI Divergence Detected!
        """
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage" # Fixed: removed space
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(url, data=payload)
            if response.status_code != 200:
                print(f"❌ Telegram API Error: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")

    def scan_all_coins(self):
        """Scan all coins for divergence"""
        print(f"🔄 Starting 1-minute scan for {len(self.symbols)} coins...")
        
        for symbol in self.symbols:
            try:
                # Fetch 1-minute candles (last 50 minutes to ensure enough data for RSI calculation)
                ohlcv = self.exchange.fetch_ohlcv(symbol, '1m', limit=50)
                
                if len(ohlcv) < 30:  # Need enough data points
                    print(f"⚠️  Not enough data for {symbol}, skipping...")
                    continue
                
                # Convert to DataFrame
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['symbol'] = symbol
                df['timeframe'] = '1m' # Add timeframe column
                
                # Detect divergence
                divergence = self.detect_divergence(df)
                if divergence:
                    print(f"✅ Divergence found: {symbol} on {divergence['tf']} at {divergence['time']}")
                    self.send_notification(divergence)
                    
            except Exception as e:
                print(f"❌ Error scanning {symbol}: {e}")
                continue # Continue to next symbol even if one fails
        
        print("🔄 Scan completed")

    def run(self):
        """Run continuous scanning every 30 seconds"""
        print("🚀 RSI Divergence Scanner Started (1-minute top 20 mode)")
        print("⏰ Scanning top 20 coins every 30 seconds...")
        while True:
            try:
                self.scan_all_coins()
                print(f"⏰ Waiting 30 seconds before next scan...")
                time.sleep(30)  # Wait 30 seconds
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                break
            except Exception as e:
                print(f"❌ Bot error: {e}")
                time.sleep(10)  # Wait 10 seconds before retry on major error

# 🚀 Run the bot
if __name__ == "__main__":
    scanner = RsiDivergenceScanner()
    scanner.run()
