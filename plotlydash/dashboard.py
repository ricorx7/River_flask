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


def create_dashboard(server):
    """Create a Plotly Dash dashboard."""
    dash_app = Dash(
        server=server,
        routes_pathname_prefix='/dashapp/',
        external_stylesheets=[
            '/static/css/styles.css',
        ]
    )

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
        X.append(X[-1] + 1)
        Y.append(Y[-1] + Y[-1] * random.uniform(-0.1, 0.1))

        data = plotly.graph_objs.Scatter(
            x=list(X),
            y=list(Y),
            name='Scatter',
            mode='lines+markers'
        )

        return {'data': [data], 'layout': go.Layout(xaxis=dict(range=[min(X), max(X)]),
                                                    yaxis=dict(range=[min(Y), max(Y)]), )}

    return dash_app.server
