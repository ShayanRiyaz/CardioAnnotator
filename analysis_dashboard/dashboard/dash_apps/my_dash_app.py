from dash import html, dcc
import dash_bootstrap_components as dbc
from django_plotly_dash import DjangoDash
from .layout import serve_layout
from dash import html, dcc, callback_context
from dash.dependencies import Input, Output, State
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from .dummy_data import generate_shared_axis_figure
from .config import WIN_LEN_SEC, FS, WIN_SAMPLES, NUM_WINDOWS,session

# Init Dash app
app = DjangoDash("SignalAnnotator", external_stylesheets=[dbc.themes.BOOTSTRAP],serve_locally=False)
app.layout = serve_layout


# Navigation callback
@app.callback(
    Output('current-window','data'),
    [Input('prev-window-btn','n_clicks_timestamp'),
     Input('next-window-btn','n_clicks_timestamp'),
     Input('jump-go-btn','n_clicks_timestamp')],
    [State('current-window','data'),
     State('jump-to-input','value')]
)
def navigate(prev_ts, next_ts, go_ts, current_idx, jump_sec):
    # build a dict of timestamps
    times = {
        'prev': prev_ts or 0,
        'next': next_ts or 0,
        'go':   go_ts   or 0
    }
    # figure out which button most recently clicked
    last = max(times, key=times.get)

    if times[last] == 0:
        return current_idx  # nothing clicked yet

    if last == 'prev':
        return max(current_idx - 1, 0)
    elif last == 'next':
        return min(current_idx + 1, NUM_WINDOWS - 1)
    else:  # 'go'
        if jump_sec is None or jump_sec < 0:
            return current_idx
        idx = int((jump_sec * FS) // WIN_SAMPLES)
        return max(0, min(idx, NUM_WINDOWS - 1))
# Update plot callback
@app.callback(
    Output('signal-plots','figure'),  # MATCHES layout
    Input('current-window','data')
)
def update_plots(window_idx):
    # Replace the following with real session data loading:
    # session = load_subject_session(...)
    # ecg = session.signals['ecg'][start:end]; etc.
    start = window_idx * WIN_SAMPLES
    end   = start + WIN_SAMPLES

    t = session.signals['t'][start:end]
    ecg = session.signals['ecg'][start:end]
    ppg = session.signals['ppg'][start:end]
    abp = session.signals['abp'][start:end]

    return generate_shared_axis_figure(ecg, ppg, abp, t)
