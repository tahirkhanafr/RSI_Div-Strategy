import ccxt
import pandas as pd
import time
import os
from datetime import datetime
import requests
import numpy as np
 
# ============================================================
# 🔔 Telegram Setup — use environment variables for security
# On PythonAnywhere: set these in the "Tasks" env or .env file
# ============================================================
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '7842209631:AAGs8BbVmUrpaA7nlGpq9IqXKqQvOM9Dr1Q')
TELEGRAM_CHAT_ID   = os.environ.get('TELEGRAM_CHAT_ID',   '1771875777')
 
 
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
        all_usdt_symbols = [
            symbol for symbol in markets.keys()
            if symbol.endswith('/USDT') and
               not any(x in symbol for x in ['UP', 'DOWN', 'BULL', 'BEAR'])
        ]
 
        top_300_symbols = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT',
            'SOL/USDT', 'DOGE/USDT', 'TRX/USDT', 'TON/USDT', 'AVAX/USDT',
            'SHIB/USDT', 'DOT/USDT', 'MATIC/USDT', 'LTC/USDT', 'BCH/USDT',
            'LINK/USDT', 'FET/USDT', 'UNI/USDT', 'ETC/USDT', 'XLM/USDT',
            'VET/USDT', 'ATOM/USDT', 'FIL/USDT', 'NEAR/USDT', 'ALGO/USDT',
            'ICP/USDT', 'HBAR/USDT', 'QNT/USDT', 'APE/USDT', 'SAND/USDT',
            'MANA/USDT', 'AXS/USDT', 'GRT/USDT', 'THETA/USDT', 'EGLD/USDT',
            'CAKE/USDT', 'AAVE/USDT', 'MKR/USDT', 'SNX/USDT', 'COMP/USDT',
            'YFI/USDT', 'SUSHI/USDT', 'CRV/USDT', 'ZEC/USDT', 'DASH/USDT',
            'XMR/USDT', 'BAT/USDT', 'ENJ/USDT', 'CHZ/USDT', 'SUI/USDT',
            'OP/USDT', 'ARB/USDT', 'TIA/USDT', 'SEI/USDT', 'INJ/USDT',
            'RUNE/USDT', 'KAS/USDT', 'APT/USDT', 'STX/USDT', 'IMX/USDT',
            'LDO/USDT', 'PEPE/USDT', 'TAO/USDT', 'CRO/USDT', 'FTM/USDT',
            'FLOKI/USDT', 'JASMY/USDT', 'BONK/USDT', 'ORDI/USDT', 'WLD/USDT',
            'ANKR/USDT', 'LRC/USDT', 'KNC/USDT', 'ZRX/USDT', '1INCH/USDT',
            'BAL/USDT', 'BNT/USDT', 'REN/USDT', 'OCEAN/USDT', 'RLC/USDT',
            'GLM/USDT', 'STORJ/USDT', 'SC/USDT', 'DGB/USDT', 'RVN/USDT',
            'CKB/USDT', 'ONE/USDT', 'IOST/USDT', 'ONT/USDT', 'NEO/USDT',
            'QTUM/USDT', 'ICX/USDT', 'WAVES/USDT', 'ZIL/USDT', 'HOT/USDT',
            'DENT/USDT', 'WIN/USDT', 'BTT/USDT', 'JST/USDT', 'SUN/USDT',
            'CELR/USDT', 'PHA/USDT', 'ENS/USDT', 'LUNC/USDT', 'DYDX/USDT',
            'GMX/USDT', 'GLMR/USDT', 'KSM/USDT', 'ARKM/USDT', 'PENDLE/USDT',
            'JUP/USDT', 'STRK/USDT', 'ZK/USDT', 'ZRO/USDT', 'EIGEN/USDT',
            'KAITO/USDT', 'VIRTUAL/USDT', 'DRIFT/USDT', 'GRASS/USDT',
            'MOODENG/USDT', 'GOAT/USDT', 'PENGU/USDT', 'PNUT/USDT',
            'RENDER/USDT', 'HYPE/USDT', 'ONDO/USDT', 'ENA/USDT', 'W/USDT',
            'ETHFI/USDT', 'BOME/USDT', 'MEW/USDT', 'POPCAT/USDT', 'POL/USDT',
            'OM/USDT', 'ROSE/USDT', 'WOO/USDT', 'GALA/USDT', 'MAGIC/USDT',
            'CYBER/USDT', 'MEME/USDT', 'JTO/USDT', 'XAI/USDT', 'PORTAL/USDT',
            'METIS/USDT', 'AEVO/USDT', 'SAGA/USDT', 'NOT/USDT', 'LISTA/USDT',
            'TRUMP/USDT', 'ANIME/USDT', 'PAXG/USDT', 'KDA/USDT', 'STG/USDT',
            'HOOK/USDT', 'EDU/USDT', 'NTRN/USDT', 'ACE/USDT', 'NFP/USDT',
            'AXL/USDT', 'BB/USDT', 'IO/USDT', 'ORDER/USDT', 'SCR/USDT',
            'SWELL/USDT', 'ME/USDT', 'ACT/USDT', 'FARTCOIN/USDT',
        ]
 
        # Filter to only symbols available on Binance
        self.symbols = [s for s in top_300_symbols if s in all_usdt_symbols]
 
        # Timeframes to scan
        self.timeframes = {
            '15m': {'ccxt': '15m', 'limit': 100},
            '30m': {'ccxt': '30m', 'limit': 80},
            '1h':  {'ccxt': '1h',  'limit': 60},
            '4h':  {'ccxt': '4h',  'limit': 40},
            '1d':  {'ccxt': '1d',  'limit': 30},
        }
 
        print(f"📊 Loaded {len(self.symbols)} symbols to scan")
        print(f"   ALL TIMEFRAMES scanned every 15 minutes")
 
    # ----------------------------------------------------------
    def calculate_rsi(self, closes, period=14):
        """Calculate RSI using Wilder's smoothing"""
        if len(closes) < period + 1:
            return [None] * len(closes)
 
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
        gains  = [max(0,  d) for d in deltas]
        losses = [max(0, -d) for d in deltas]
 
        rsis = [None] * period
 
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        rsis.append(100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss)))
 
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i])  / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            rsis.append(100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss)))
 
        assert len(rsis) == len(closes)
        return rsis
 
    # ----------------------------------------------------------
    def calculate_obv(self, df):
        """Calculate On-Balance Volume"""
        obv    = [0]
        volume = df['volume'].tolist()
        close  = df['close'].tolist()
 
        for i in range(1, len(close)):
            if close[i] > close[i - 1]:
                obv.append(obv[-1] + volume[i])
            elif close[i] < close[i - 1]:
                obv.append(obv[-1] - volume[i])
            else:
                obv.append(obv[-1])
        return obv
 
    # ----------------------------------------------------------
    def find_swings(self, series):
        """Find swing lows in a series"""
        swings = []
        for i in range(1, len(series) - 1):
            val, prev_val, next_val = series[i], series[i - 1], series[i + 1]
            if val is not None and prev_val is not None and next_val is not None:
                if val < prev_val and val < next_val:
                    swings.append((i, val))
        return swings
 
    # ----------------------------------------------------------
    def detect_divergence(self, df, timeframe):
        """Detect RSI and/or OBV bullish divergence"""
        closes     = df['close'].tolist()
        rsi_values = self.calculate_rsi(closes)
        obv_values = self.calculate_obv(df)
 
        df['rsi'] = rsi_values
        df['obv'] = obv_values
 
        price_lows = self.find_swings(df['low'].tolist())
        rsi_lows   = self.find_swings(rsi_values)
        obv_lows   = self.find_swings(obv_values)
 
        price_low_dict = dict(price_lows)
        rsi_low_dict   = dict(rsi_lows)
        obv_low_dict   = dict(obv_lows)
 
        recent_divergences = []
        df_len = len(df)
 
        for i in range(len(price_lows) - 1):
            for j in range(i + 1, min(i + 10, len(price_lows))):
                idx1, price1 = price_lows[i]
                idx2, price2 = price_lows[j]
 
                if idx2 < df_len - 5:
                    continue
                dist = idx2 - idx1
                if dist < 5 or dist > 25:
                    continue
                if price2 >= price1:
                    continue
 
                rsi1 = rsi_low_dict.get(idx1)
                rsi2 = rsi_low_dict.get(idx2)
                obv1 = obv_low_dict.get(idx1)
                obv2 = obv_low_dict.get(idx2)
 
                if any(v is None for v in [rsi1, rsi2, obv1, obv2]):
                    continue
 
                current_price = df['close'].iloc[-1]
                interim_high  = df['high'].iloc[idx1:idx2 + 1].max()
                risk          = current_price - price2
                target        = current_price + (risk * 2)
 
                has_rsi_div = rsi1 < 35 and rsi2 < 35 and rsi2 > rsi1 + 1.5
                has_obv_div = obv2 > obv1
                confidence  = 0
 
                if has_rsi_div:
                    confidence += 4
                if has_obv_div:
                    confidence += 4
                if not (has_rsi_div or has_obv_div):
                    continue
                if has_rsi_div and has_obv_div:
                    signal_type = "STRONG RSI+OBV"
                    confidence += 2
                elif has_rsi_div:
                    signal_type = "RSI ONLY"
                    confidence += 1
                else:
                    signal_type = "OBV ONLY"
                    confidence += 1
 
                confidence = min(10, confidence)
 
                recent_divergences.append({
                    'symbol':        df['symbol'].iloc[0],
                    'time':          datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'tf':            timeframe,
                    'rsi1':          round(rsi1, 2),
                    'rsi2':          round(rsi2, 2),
                    'obv1':          round(obv1, 0),
                    'obv2':          round(obv2, 0),
                    'price1':        round(price1, 6),
                    'price2':        round(price2, 6),
                    'distance':      dist,
                    'current_price': round(current_price, 6),
                    'interim_high':  round(interim_high, 6),
                    'stop_loss':     round(price2 * 0.999, 6),
                    'take_profit':   round(target, 6),
                    'confidence':    confidence,
                    'signal_type':   signal_type,
                    'has_rsi_div':   has_rsi_div,
                    'has_obv_div':   has_obv_div,
                })
 
        if recent_divergences:
            return max(recent_divergences, key=lambda x: x['confidence'])
        return None
 
    # ----------------------------------------------------------
    def send_notification(self, divergence):
        """Send Telegram notification with trade plan"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️  No Telegram credentials. Skipping notification.")
            return
 
        signal_emoji = (
            "⭐" if divergence['confidence'] >= 8 else
            "⚡" if divergence['confidence'] >= 6 else
            "🔍"
        )
        tf_emoji = {
            '15m': '🕒', '30m': '⏱️', '1h': '🕐', '4h': '🕓', '1d': '📅'
        }.get(divergence['tf'], '⏰')
 
        message = f"""
{signal_emoji} {tf_emoji} <b>🚨 {divergence['signal_type']} Bullish Divergence Alert! ({divergence['tf'].upper()})</b>
 
📊 <b>Symbol:</b> {divergence['symbol']}
⏱️ <b>Timeframe:</b> {divergence['tf'].upper()}
⏰ <b>Detection Time:</b> {divergence['time']}
⭐ <b>Signal Strength:</b> {divergence['confidence']}/10
 
📉 <b>Price Low 1:</b> ${divergence['price1']}
📉 <b>Price Low 2:</b> ${divergence['price2']} (Lower low confirmed)
📏 <b>Distance:</b> {divergence['distance']} bars
💎 <b>Current Price:</b> ${divergence['current_price']}
 
{'✅ <b>RSI Divergence:</b> ' + str(divergence['rsi1']) + ' → ' + str(divergence['rsi2']) if divergence['has_rsi_div'] else '❌ <b>RSI Divergence:</b> Not detected'}
{'✅ <b>OBV Divergence:</b> ' + str(int(divergence['obv1'])) + ' → ' + str(int(divergence['obv2'])) if divergence['has_obv_div'] else '❌ <b>OBV Divergence:</b> Not detected'}
 
🧠 <b>Strategy Insight:</b>
{'✅ RSI shows oversold momentum shift!' if divergence['has_rsi_div'] else ''}
{'✅ OBV confirms volume accumulation!' if divergence['has_obv_div'] else ''}
{'🎯 STRONG CONFIRMATION: Both indicators aligned!' if divergence['has_rsi_div'] and divergence['has_obv_div'] else ''}
 
🎯 <b>Trade Plan (1:2 RR):</b>
• <b>Entry:</b> Break above interim high ${divergence['interim_high']} (bullish close)
• <b>Stop Loss:</b> Below recent low ${divergence['stop_loss']} (risk ~{round((divergence['current_price'] - divergence['stop_loss']) / divergence['current_price'] * 100, 2)}%)
• <b>Take Profit:</b> ${divergence['take_profit']}
 
⚠️ <b>Risk 1% per trade. DYOR — markets can fake out!</b>
✅ <i>From your Multi-Timeframe RSI+OBV Divergence Scanner</i>
        """
 
        url     = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code != 200:
                print(f"❌ Telegram Error: {response.status_code} — {response.text}")
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")
 
    # ----------------------------------------------------------
    def scan_all_timeframes(self):
        """Scan ALL timeframes for all coins every 15 minutes"""
        print(f"\n{'='*60}")
        print(f"⏰ FULL SCAN STARTED at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔄 Scanning {len(self.timeframes)} timeframes × {len(self.symbols)} coins...")
        print(f"{'='*60}")
 
        total_signals = 0
        rsi_signals   = 0
        obv_signals   = 0
        scan_start    = time.time()
 
        for tf_name, tf_config in self.timeframes.items():
            print(f"\n🔍 Scanning {tf_name.upper()} timeframe...")
            tf_signals = 0
 
            for symbol in self.symbols:
                try:
                    ohlcv = self.exchange.fetch_ohlcv(
                        symbol, tf_config['ccxt'], limit=tf_config['limit']
                    )
 
                    # ✅ FIX: rate-limit buffer between API calls
                    time.sleep(0.15)
 
                    if len(ohlcv) < tf_config['limit'] * 0.5:
                        continue
 
                    df = pd.DataFrame(
                        ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    df['symbol']    = symbol
                    df['timeframe'] = tf_name
 
                    divergence = self.detect_divergence(df, tf_name)
                    if divergence:
                        conf = divergence['confidence']
                        strength = (
                            "🔥 STRONG"   if conf >= 7 else
                            "⚡ MODERATE" if conf >= 5 else
                            "🔍 WEAK"
                        )
                        print(
                            f"  ✅ {strength} | {symbol} | {divergence['signal_type']} "
                            f"| Conf: {conf}/10 | [{divergence['time']}]"
                        )
                        self.send_notification(divergence)
                        tf_signals    += 1
                        total_signals += 1
                        if divergence['has_rsi_div']:
                            rsi_signals += 1
                        if divergence['has_obv_div']:
                            obv_signals += 1
 
                except Exception as e:
                    # Log errors but keep scanning
                    print(f"  ⚠️  Error on {symbol} / {tf_name}: {e}")
                    continue
 
            if tf_signals == 0:
                print(f"   ❌ No divergences found on {tf_name.upper()}")
 
        duration = time.time() - scan_start
        print(f"\n{'='*60}")
        print(f"✅ FULL SCAN COMPLETED in {duration:.2f} seconds")
        print(f"📈 Total signals : {total_signals}")
        print(f"📊 RSI signals   : {rsi_signals}")
        print(f"📊 OBV signals   : {obv_signals}")
        print(f"✅ Last scan     : {time.strftime('%d %b %Y, %H:%M:%S')}")
        print(f"😴 Next scan in 15 minutes...")
        print(f"{'='*60}")
 
    # ----------------------------------------------------------
    def run_continuous(self):
        """Run continuous scanning every 15 minutes"""
        print("🚀 Multi-Timeframe RSI+OBV Divergence Scanner started")
        print("⏰ Scanning 15m / 30m / 1h / 4h / 1d every 15 minutes\n")
 
        while True:
            try:
                self.scan_all_timeframes()
                time.sleep(900)  # 15 minutes
            except KeyboardInterrupt:
                print("\n🛑 Scanner stopped by user.")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                time.sleep(10)
 
 
# 🚀 Entry point
if __name__ == "__main__":
    scanner = RsiDivergenceScanner()
    scanner.run_continuous()
