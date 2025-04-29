import pandas as pd
import numpy as np
from scipy import stats
from pypfopt import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns

class PortfolioAnalyzer:
    def __init__(self, asset_data: dict, weights: dict):
        """
        Initialize with asset price data and portfolio weights
        """
        self.asset_data = asset_data
        self.weights = weights
        self.risk_free_rate = 0.03  # Assuming 3% risk-free rate
        
    def calculate_returns(self) -> pd.DataFrame:
        """
        Calculate daily returns for all assets
        """
        returns_dict = {}
        for symbol, data in self.asset_data.items():
            returns_dict[symbol] = data['Close'].pct_change()
        return pd.DataFrame(returns_dict)

    def calculate_portfolio_value(self, initial_investment: float) -> pd.DataFrame:
        """
        Calculate portfolio value over time
        """
        returns = self.calculate_returns()
        weighted_returns = returns.mul(pd.Series(self.weights))
        portfolio_returns = weighted_returns.sum(axis=1)
        portfolio_value = (1 + portfolio_returns).cumprod() * initial_investment
        return portfolio_value

    def calculate_risk_metrics(self) -> dict:
        """
        Calculate various risk metrics
        """
        returns = self.calculate_returns()
        portfolio_returns = (returns * pd.Series(self.weights)).sum(axis=1)
        
        # Annualized metrics
        annual_return = portfolio_returns.mean() * 252
        annual_volatility = portfolio_returns.std() * np.sqrt(252)
        
        # Sharpe Ratio
        excess_returns = portfolio_returns - self.risk_free_rate/252
        sharpe_ratio = np.sqrt(252) * excess_returns.mean() / portfolio_returns.std()
        
        # Sortino Ratio
        negative_returns = portfolio_returns[portfolio_returns < 0]
        downside_std = negative_returns.std() * np.sqrt(252)
        sortino_ratio = annual_return / downside_std if downside_std != 0 else np.nan
        
        # Value at Risk (VaR)
        var_95 = stats.norm.ppf(0.05, portfolio_returns.mean(), portfolio_returns.std())
        
        return {
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'var_95': var_95
        }

    def optimize_portfolio(self) -> dict:
        """
        Perform mean-variance optimization
        """
        # Prepare price data
        prices = pd.DataFrame({symbol: data['Close'] for symbol, data in self.asset_data.items()})
        
        # Calculate expected returns and sample covariance
        mu = expected_returns.mean_historical_return(prices)
        S = risk_models.sample_cov(prices)
        
        # Optimize for maximum Sharpe Ratio
        ef = EfficientFrontier(mu, S)
        weights = ef.max_sharpe()
        cleaned_weights = ef.clean_weights()
        
        # Calculate performance metrics
        performance = ef.portfolio_performance(verbose=True)
        
        return {
            'optimal_weights': cleaned_weights,
            'expected_return': performance[0],
            'volatility': performance[1],
            'sharpe_ratio': performance[2]
        }

    def check_rebalancing_needs(self, threshold: float = 0.05) -> dict:
        """
        Check if portfolio needs rebalancing
        """
        current_weights = {}
        total_value = 0
        
        # Calculate current portfolio value and weights
        for symbol, data in self.asset_data.items():
            current_price = data['Close'].iloc[-1]
            position_value = current_price * self.weights[symbol]
            total_value += position_value
            current_weights[symbol] = position_value
        
        # Convert to percentages
        current_weights = {k: v/total_value for k, v in current_weights.items()}
        
        # Check for drift
        drift = {}
        rebalance_needed = False
        for symbol in self.weights:
            drift[symbol] = current_weights[symbol] - self.weights[symbol]
            if abs(drift[symbol]) > threshold:
                rebalance_needed = True
        
        return {
            'rebalance_needed': rebalance_needed,
            'current_weights': current_weights,
            'drift': drift,
            'target_weights': self.weights
        }

    def get_rebalancing_trades(self, portfolio_value: float) -> dict:
        """
        Calculate required trades for rebalancing
        """
        rebalance_info = self.check_rebalancing_needs()
        if not rebalance_info['rebalance_needed']:
            return {}
        
        trades = {}
        for symbol in self.weights:
            current_value = portfolio_value * rebalance_info['current_weights'][symbol]
            target_value = portfolio_value * self.weights[symbol]
            trade_value = target_value - current_value
            
            current_price = self.asset_data[symbol]['Close'].iloc[-1]
            trade_units = trade_value / current_price
            
            trades[symbol] = {
                'units': trade_units,
                'value': trade_value,
                'action': 'buy' if trade_value > 0 else 'sell'
            }
        
        return trades
