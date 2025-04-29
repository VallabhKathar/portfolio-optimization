import yfinance as yf
import pandas as pd
import numpy as np
from nsepy import get_history
from datetime import datetime, timedelta
import requests

class DataFetcher:
    def __init__(self):
        self.crypto_base_url = "https://api.coingecko.com/api/v3"
        
    def fetch_stock_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch Indian stock data using NSEpy
        """
        try:
            # For NSE stocks, remove the .NS suffix if present
            clean_symbol = symbol.replace('.NS', '')
            data = get_history(symbol=clean_symbol,
                             start=start_date,
                             end=end_date)
            data = data[['Close', 'High', 'Low', 'Open', 'Volume']]
            return data
        except Exception as e:
            print(f"Error fetching stock data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def fetch_crypto_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch cryptocurrency data using CoinGecko API
        """
        try:
            # Convert symbol to CoinGecko format (e.g., BTC-USD to bitcoin)
            coin_id = self._get_coin_id(symbol)
            if not coin_id:
                return pd.DataFrame()

            # Convert dates to Unix timestamps
            start_ts = int(start_date.timestamp())
            end_ts = int(end_date.timestamp())

            url = f"{self.crypto_base_url}/coins/{coin_id}/market_chart/range"
            params = {
                'vs_currency': 'usd',
                'from': start_ts,
                'to': end_ts
            }

            response = requests.get(url, params=params)
            data = response.json()

            # Create DataFrame from price data
            df = pd.DataFrame(data['prices'], columns=['timestamp', 'Close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df

        except Exception as e:
            print(f"Error fetching crypto data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def fetch_gold_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Fetch gold price data using yfinance
        """
        try:
            # Use GC=F for gold futures
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            return data[['Close', 'High', 'Low', 'Open', 'Volume']]
        except Exception as e:
            print(f"Error fetching gold data: {str(e)}")
            return pd.DataFrame()

    def fetch_all_assets(self, portfolio: dict, start_date: datetime, end_date: datetime) -> dict:
        """
        Fetch data for all assets in the portfolio
        """
        asset_data = {}
        
        for asset_type, assets in portfolio.items():
            for symbol in assets:
                if asset_type == 'stocks':
                    data = self.fetch_stock_data(symbol, start_date, end_date)
                elif asset_type == 'crypto':
                    data = self.fetch_crypto_data(symbol, start_date, end_date)
                elif asset_type == 'commodities':
                    data = self.fetch_gold_data(symbol, start_date, end_date)
                
                if not data.empty:
                    asset_data[symbol] = data
                
        return asset_data

    def _get_coin_id(self, symbol: str) -> str:
        """
        Convert crypto symbol to CoinGecko coin ID
        """
        # Common mappings
        symbol_to_id = {
            'BTC-USD': 'bitcoin',
            'ETH-USD': 'ethereum',
            'USDT-USD': 'tether',
            'BNB-USD': 'binancecoin',
            'XRP-USD': 'ripple'
        }
        
        return symbol_to_id.get(symbol, '') 
