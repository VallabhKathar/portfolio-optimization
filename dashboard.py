import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class Dashboard:
    def __init__(self, data_fetcher, portfolio_analyzer):
        self.data_fetcher = data_fetcher
        self.portfolio_analyzer = portfolio_analyzer

    def run(self):
        st.set_page_config(page_title="Portfolio Optimization Dashboard", layout="wide")
        st.title("Portfolio Optimization Dashboard")

        # Sidebar for user inputs
        self._create_sidebar()

        # Main dashboard layout
        col1, col2 = st.columns([2, 1])

        with col1:
            self._show_portfolio_overview()
            self._show_performance_charts()

        with col2:
            self._show_risk_metrics()
            self._show_rebalancing_alerts()

    def _create_sidebar(self):
        st.sidebar.header("Portfolio Settings")

        # Asset Input Section
        st.sidebar.subheader("Asset Holdings")
        
        # Stocks
        st.sidebar.text("Indian Stocks (e.g., RELIANCE.NS)")
        stock_symbols = st.sidebar.text_input("Enter stock symbols (comma-separated)")
        
        # Crypto
        st.sidebar.text("Cryptocurrencies (e.g., BTC-USD)")
        crypto_symbols = st.sidebar.text_input("Enter crypto symbols (comma-separated)")
        
        # Commodities
        st.sidebar.text("Commodities (e.g., GC=F)")
        commodity_symbols = st.sidebar.text_input("Enter commodity symbols (comma-separated)")

        # Weights Input
        st.sidebar.subheader("Portfolio Weights")
        weights = {}
        
        if stock_symbols:
            for symbol in stock_symbols.split(','):
                symbol = symbol.strip()
                weights[symbol] = st.sidebar.number_input(f"Weight for {symbol}", 0.0, 1.0, 0.1)

        if crypto_symbols:
            for symbol in crypto_symbols.split(','):
                symbol = symbol.strip()
                weights[symbol] = st.sidebar.number_input(f"Weight for {symbol}", 0.0, 1.0, 0.1)

        if commodity_symbols:
            for symbol in commodity_symbols.split(','):
                symbol = symbol.strip()
                weights[symbol] = st.sidebar.number_input(f"Weight for {symbol}", 0.0, 1.0, 0.1)

        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}

        # Store in session state
        st.session_state['weights'] = weights
        st.session_state['portfolio'] = {
            'stocks': [s.strip() for s in stock_symbols.split(',') if s.strip()],
            'crypto': [s.strip() for s in crypto_symbols.split(',') if s.strip()],
            'commodities': [s.strip() for s in commodity_symbols.split(',') if s.strip()]
        }

    def _show_portfolio_overview(self):
        st.subheader("Portfolio Allocation")
        
        if 'weights' in st.session_state and st.session_state['weights']:
            weights = st.session_state['weights']
            
            # Create pie chart
            fig = go.Figure(data=[go.Pie(
                labels=list(weights.keys()),
                values=list(weights.values()),
                hole=.3
            )])
            
            fig.update_layout(title="Current Portfolio Allocation")
            st.plotly_chart(fig)
        else:
            st.info("Please input your portfolio holdings in the sidebar.")

    def _show_performance_charts(self):
        st.subheader("Portfolio Performance")
        
        if 'weights' in st.session_state and st.session_state['weights']:
            # Calculate portfolio value
            portfolio_value = self.portfolio_analyzer.calculate_portfolio_value(100000)  # Assuming 100k initial investment
            
            # Create line chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=portfolio_value.index,
                y=portfolio_value.values,
                mode='lines',
                name='Portfolio Value'
            ))
            
            fig.update_layout(
                title="Portfolio Value Over Time",
                xaxis_title="Date",
                yaxis_title="Value ($)"
            )
            
            st.plotly_chart(fig)

    def _show_risk_metrics(self):
        st.subheader("Risk Metrics")
        
        if 'weights' in st.session_state and st.session_state['weights']:
            metrics = self.portfolio_analyzer.calculate_risk_metrics()
            
            # Display metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Annual Return", f"{metrics['annual_return']:.2%}")
                st.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")
            
            with col2:
                st.metric("Annual Volatility", f"{metrics['annual_volatility']:.2%}")
                st.metric("VaR (95%)", f"{metrics['var_95']:.2%}")

    def _show_rebalancing_alerts(self):
        st.subheader("Rebalancing Analysis")
        
        if 'weights' in st.session_state and st.session_state['weights']:
            rebalance_info = self.portfolio_analyzer.check_rebalancing_needs()
            
            if rebalance_info['rebalance_needed']:
                st.warning("Portfolio requires rebalancing!")
                
                # Show drift table
                drift_df = pd.DataFrame({
                    'Current Weight': rebalance_info['current_weights'],
                    'Target Weight': rebalance_info['target_weights'],
                    'Drift': rebalance_info['drift']
                })
                
                st.dataframe(drift_df)
                
                # Show optimization suggestion
                if st.button("Get Optimization Suggestion"):
                    opt_result = self.portfolio_analyzer.optimize_portfolio()
                    st.write("Suggested optimal weights:")
                    st.write(pd.Series(opt_result['optimal_weights']))
                    
                    metrics = [
                        f"Expected Return: {opt_result['expected_return']:.2%}",
                        f"Volatility: {opt_result['volatility']:.2%}",
                        f"Sharpe Ratio: {opt_result['sharpe_ratio']:.2f}"
                    ]
                    st.write("\n".join(metrics))
            else:
                st.success("Portfolio is properly balanced.")
