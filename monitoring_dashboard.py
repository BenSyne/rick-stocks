import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from brokerage_api_integration import BrokerageAPIIntegration
from performance_metrics_calculator import PerformanceMetricsCalculator

class MonitoringDashboard:
    def __init__(self, brokerage_api: BrokerageAPIIntegration, performance_metrics_calculator: PerformanceMetricsCalculator):
        self.brokerage_api = brokerage_api
        self.performance_metrics_calculator = performance_metrics_calculator
        self.app = dash.Dash(__name__)

    def layout(self):
        self.app.layout = html.Div([
            html.H1('Live Trading Monitoring Dashboard'),
            dcc.Interval(
                id='interval-component',
                interval=1*1000, # in milliseconds
                n_intervals=0
            ),
            html.Div(id='live-update-text'),
            dcc.Graph(id='live-update-graph'),
        ])

    def update_metrics(self):
        # # Fetch real-time metrics
        # portfolio = self.brokerage_api.get_portfolio()
        # roi = self.performance_metrics_calculator.calculate_roi(portfolio)
        # sharpe_ratio = self.performance_metrics_calculator.calculate_sharpe_ratio(portfolio)
        # drawdown = self.performance_metrics_calculator.calculate_max_drawdown(portfolio)

        style = {'padding': '5px', 'fontSize': '16px'}
        return [
            html.Span('ROI: {0:.2f}%'.format(roi*100), style=style),
            html.Span('Sharpe Ratio: {0:.2f}'.format(sharpe_ratio), style=style),
            html.Span('Max Drawdown: {0:.2f}%'.format(drawdown*100), style=style),
        ]

    def update_graph(self):
        # Fetch real-time data
        data = self.brokerage_api.get_realtime_data()

        # Create the graph 
        fig = go.Figure(data=[
            go.Candlestick(
                x=data['date'],
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close']
            )
        ])

        return fig

    def callbacks(self):
        @self.app.callback(Output('live-update-text', 'children'),
                      [Input('interval-component', 'n_intervals')])
        def update_metrics(n):
            return self.update_metrics()

        @self.app.callback(Output('live-update-graph', 'figure'),
                      [Input('interval-component', 'n_intervals')])
        def update_graph_live(n):
            return self.update_graph()

    def run(self):
        self.layout()
        self.callbacks()
        self.app.run_server(debug=True)

if __name__ == "__main__":
    brokerage_api = BrokerageAPIIntegration()
    performance_metrics_calculator = PerformanceMetricsCalculator()
    dashboard = MonitoringDashboard(brokerage_api, performance_metrics_calculator)
    dashboard.run()

