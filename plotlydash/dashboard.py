from dash import Dash
import dash_html_components as html
import dash
from dash.dependencies import Output, State, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
from collections import deque

X = deque(maxlen=20)
X.append(1)
Y = deque(maxlen=20)
Y.append(1)


class Dashboard:

    def __init__(self):
        self.datetime_queue = deque(maxlen=100)
        self.systemp_queue = deque(maxlen=100)
        self.datetime_queue.append(1)   # Temp data until real data comes
        self.systemp_queue.append(1)    # Temp data until real data comes
        self.is_data_received = False

    def create_dashboard(self, server):
        """Create a Plotly Dash dashboard."""
        dash_app = Dash(
            server=server,                                          # Connect to Flask Server
            routes_pathname_prefix='/dashapp/',                     # Path to dashboard
            external_stylesheets=['/static/css/styles.css', ]       # style sheet
        )

        # Create the Dashboard layout
        dash_app.layout = html.Div(
            [
                dcc.Graph(id='live-graph', animate=True),
                dcc.Interval(
                    id='graph-update',
                    interval=1 * 1000
                ),
            ]
        )

        @dash_app.callback(Output('live-graph', 'figure'), [Input("graph-update", "n_intervals")], )
        def update_graph_scatter(n):

            data = plotly.graph_objs.Scatter(
                x=list(self.datetime_queue),
                y=list(self.systemp_queue),
                name='Temperature',
                mode='lines+markers'
            )

            return {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(self.datetime_queue), max(self.datetime_queue)]),
                                                        yaxis=dict(range=[min(self.systemp_queue), max(self.systemp_queue)]), )}

        return dash_app.server

    def add_ens(self, ens):
        if ens.IsEnsembleData and ens.IsAncillaryData:
            # Remove the temporary data when we get any data
            if not self.is_data_received:
                self.datetime_queue.clear()
                self.systemp_queue.clear()
                self.is_data_received = True

            # Add data to the queue
            self.datetime_queue.append(ens.EnsembleData.datetime().strftime("%Y-%m-%d %H:%M:%S.%f"))
            self.systemp_queue.append(ens.AncillaryData.SystemTemp)


