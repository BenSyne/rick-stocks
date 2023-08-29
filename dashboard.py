import dash
import dash_core_components as dcc
# import dash_html_components as html
from dash import html
from dash.dependencies import Input, Output
from plotting_module import PlottingModule
from performance_metrics_calculator import PerformanceMetricsCalculator
from backtesting_framework import BacktestingFramework
from database_manager import DatabaseManager
from strategy_logic import ATRSignalsStrategy
from technical_indicators_generator import TechnicalIndicatorsGenerator

class Dashboard:
    def __init__(self, db_manager, plotting_module, backtesting_framework, performance_metrics_calculator):
        self.db_manager = db_manager
        self.plotting_module = plotting_module
        self.backtesting_framework = backtesting_framework
        self.performance_metrics_calculator = performance_metrics_calculator

        self.app = dash.Dash(__name__)

        self.app.layout = html.Div([
            html.H1('Trading Strategy Backtesting and Execution System'),
            dcc.Dropdown(
                id='ticker-dropdown',
                options=[{'label': ticker, 'value': ticker} for ticker in self.db_manager.get_all_tickers('tickers')],
                value='AAPL'
            ),
            dcc.DatePickerRange(
                id='date-picker',
                start_date_placeholder_text="Start Period",
                end_date_placeholder_text="End Period",
                start_date='2020-01-01',
                end_date='2021-12-31'
            ),
            html.Button('Run Backtest', id='backtest-button', n_clicks=0),
            dcc.Graph(id='stock-graph'),
            html.Div(id='performance-metrics')
        ])

        @self.app.callback(
            Output('stock-graph', 'figure'),
            [Input('ticker-dropdown', 'value'),
             Input('date-picker', 'start_date'),
             Input('date-picker', 'end_date'),
             Input('backtest-button', 'n_clicks')]
        )
        def update_graph(ticker, start_date, end_date, n_clicks):
            if n_clicks > 0:
                self.backtesting_framework.run_backtest(ticker, start_date, end_date)
            return self.plotting_module.plot_stock_data(ticker, start_date, end_date)

        @self.app.callback(
            Output('performance-metrics', 'children'),
            [Input('ticker-dropdown', 'value'),
             Input('date-picker', 'start_date'),
             Input('date-picker', 'end_date'),
             Input('backtest-button', 'n_clicks')]
        )
        def update_performance_metrics(ticker, start_date, end_date, n_clicks):
            if n_clicks > 0:
                self.backtesting_framework.run_backtest(ticker, start_date, end_date)
                roi = self.performance_metrics_calculator.calculate_roi()
                sharpe_ratio = self.performance_metrics_calculator.calculate_sharpe_ratio()
                return f'ROI: {roi}, Sharpe Ratio: {sharpe_ratio}'

    def run(self):
        self.app.run_server(debug=True)

if __name__ == '__main__':
    db_name = 'interactive_brokers_database'
    user = 'macman'
    password = 'My@oNtpd6v-WUzqBgjfA'
    db_manager = DatabaseManager(db_name, user, password)

    # Create the table if it doesn't exist
    table_name = 'tickers'  # Replace with your actual table name
    db_manager.create_table_if_not_exists(table_name)

    # Insert tickers into the table
    tickers = ['AAPL', 'GOOG', 'MSFT', 'AMZN']  # Replace with your actual list of tickers
    for ticker in tickers:
        db_manager.insert_ticker(table_name, ticker)

    # Get all tickers from the table
    tickers = db_manager.get_all_tickers(table_name)

    plotting_module = PlottingModule(db_manager)
    
    # Create an instance of TechnicalIndicatorsGenerator and pass it to ATRSignalsStrategy
    indicator_generator = TechnicalIndicatorsGenerator(db_manager)
    backtesting_framework = BacktestingFramework(db_manager, ATRSignalsStrategy(db_manager, indicator_generator))
    
    performance_metrics_calculator = PerformanceMetricsCalculator(backtesting_framework.portfolio)
    dashboard = Dashboard(db_manager, plotting_module, backtesting_framework, performance_metrics_calculator)
    dashboard.run()


    # CREATE USER macman WITH PASSWORD 'My@oNtpd6v-WUzqBgjfA'
    # GRANT ALL PRIVILEGES ON DATABASE interactive_brokers_database TO macman;
    # CREATE DATABASE interactive_brokers_database;