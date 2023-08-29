import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis

class PerformanceMetricsCalculator:
    def __init__(self, portfolio):
        self.portfolio = portfolio

    def calculate_roi(self):
        """
        Calculate Return on Investment (ROI)
        """
        initial_value = self.portfolio['total'].iloc[0]
        final_value = self.portfolio['total'].iloc[-1]
        roi = (final_value - initial_value) / initial_value
        return roi

    def calculate_sharpe_ratio(self, risk_free_rate=0.01):
        """
        Calculate Sharpe Ratio
        """
        returns = self.portfolio['returns']
        excess_returns = returns - risk_free_rate
        sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns)
        return sharpe_ratio

    def calculate_drawdown(self):
        """
        Calculate Drawdown
        """
        cumulative_returns = np.cumsum(self.portfolio['returns'])
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = running_max - cumulative_returns
        return drawdown

    def calculate_skewness(self):
        """
        Calculate Skewness
        """
        returns = self.portfolio['returns']
        skewness = skew(returns)
        return skewness

    def calculate_kurtosis(self):
        """
        Calculate Kurtosis
        """
        returns = self.portfolio['returns']
        kurtosis_val = kurtosis(returns)
        return kurtosis_val

    def calculate_all_metrics(self):
        """
        Calculate all performance metrics
        """
        metrics = {
            'ROI': self.calculate_roi(),
            'Sharpe Ratio': self.calculate_sharpe_ratio(),
            'Drawdown': self.calculate_drawdown(),
            'Skewness': self.calculate_skewness(),
            'Kurtosis': self.calculate_kurtosis()
        }
        return metrics

