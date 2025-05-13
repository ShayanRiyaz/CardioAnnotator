from dash.dependencies import Input, Output, State
import json
from dash import dcc, html
import dash_bootstrap_components as dbc
from django_plotly_dash import DjangoDash
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from .annotation_layout import serve_layout
from ..generate_shared_axis_figure import generate_shared_xaxis_figure
from ..get_data import FS, WIN_SAMPLES, NUM_WINDOWS,session,WIN_LEN_SEC

# Init Dash app
app = DjangoDash("SignalAnnotator", external_stylesheets=[dbc.themes.BOOTSTRAP],serve_locally=False)
app.layout = serve_layout

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import json
from dash import html

# 1) Navigation stays the same
@app.callback(
    Output('current-window','data'),
    [Input('prev-window-btn','n_clicks_timestamp'),
     Input('next-window-btn','n_clicks_timestamp'),
     Input('jump-go-btn','n_clicks_timestamp')],
    [State('current-window','data'),
     State('jump-to-input','value')]
)
def navigate(prev_ts, next_ts, go_ts, current_idx, jump_sec):
    times = {'prev': prev_ts or 0, 'next': next_ts or 0, 'go': go_ts or 0}
    last  = max(times, key=times.get)
    if times[last] == 0:
        return current_idx
    if last == 'prev':
        return max(current_idx - 1, 0)
    if last == 'next':
        return min(current_idx + 1, NUM_WINDOWS - 1)
    # go
    if jump_sec is None or jump_sec < 0:
        return current_idx
    idx = int((jump_sec * FS) // WIN_SAMPLES)
    return max(0, min(idx, NUM_WINDOWS - 1))

# 2) Annotation click callback
@app.callback(
    Output('annotations', 'data'),
    [
      Input('signal-plots',   'clickData'),
      Input('mode-selector',  'value'),
    ],
    [
      State('annotations',    'data'),
      State('current-window', 'data'),
    ]
)
def modify_peak(clickData, mode, annotations, window_idx):
    if not clickData:
        # Only fires when you actually click the graph
        raise PreventUpdate

    # Which trace? 0=ECG,1=PPG,2=ABP
    trace_i = clickData['points'][0]['curveNumber']
    sig     = {0: 'ecg', 1: 'ppg', 2: 'abp'}[trace_i]

    # Convert click X (sec into window) → global sample index
    peak_amplitude = clickData['points'][0]['y']
    t_rel      = clickData['points'][0]['x']
    sample_idx =  int(t_rel * FS)

    # Initialize or update your annotations dict
    ann   = annotations if isinstance(annotations, dict) else {}
    sample_peaks = ann.setdefault(sig, {}).setdefault('sample_peak_positions', [])
    time_peaks = ann.setdefault(sig, {}).setdefault('time_peak_positions', [])
    peak_amplitudes = ann.setdefault(sig, {}).setdefault('peak_amplitudes', [])

    if mode == 'add':
        if sample_idx not in sample_peaks:
            sample_peaks.append(sample_idx)
            time_peaks.append(t_rel)
            peak_amplitudes.append(peak_amplitude)
    else:  # mode == 'remove'
        sample_peaks[:] = [p for p in sample_peaks if abs(p - sample_idx) > 1]
        time_peaks[:] = [p for p in time_peaks if abs(p - time_peaks) > 1]
        time_peaks[:] = [p for p in peak_amplitudes if abs(p - peak_amplitudes) > 1]

    ann[sig]['sample_peak_positions'] = sorted(sample_peaks)
    ann[sig]['time_peak_positions'] = sorted(time_peaks)
    ann[sig]['peak_amplitudes'] = sorted(peak_amplitudes)
    return ann
# @app.callback(
#     Output('annotations', 'data'),
#     [
#       Input('signal-plots',   'clickData'),
#       Input('mode-selector',  'value'),
#       Input('current-window','data'),       # ← make this an Input
#     ],
#     [
#       State('annotations',    'data'),
#     ]
# )
# def modify_peak(clickData, mode, window_idx, annotations):

#     if not clickData:
#         raise PreventUpdate

#     # Which subplot: ECG=0, PPG=1, ABP=2
#     trace_i = clickData['points'][0]['curveNumber']
#     sig     = {0:'ecg',1:'ppg',2:'abp'}[trace_i]

#     # Convert click X (sec in window) → global sample index
#     t_rel      = clickData['points'][0]['x']
#     sample_idx = window_idx * WIN_SAMPLES + int(t_rel * FS)

#     # Initialize the store
#     ann   = annotations if isinstance(annotations, dict) else {}
#     peaks = ann.setdefault(sig, {}).setdefault('peaks', [])

#     if mode == 'add':
#         if sample_idx not in peaks:
#             peaks.append(sample_idx)
#     else:  # remove
#         peaks[:] = [p for p in peaks if abs(p - sample_idx) > 1]

#     ann[sig]['peaks'] = sorted(peaks)
#     return ann
# 3) Redraw on window or annotation change
@app.callback(
    Output('signal-plots','figure'),
    [ Input('current-window','data'),
      Input('annotations','data') ]
)
def update_plots(window_idx, annotations):
    # slice your real data
    start = window_idx * WIN_SAMPLES
    end   = start + WIN_SAMPLES
    t   = session.signals['t'][start:end]
    ecg = session.signals['ecg'][start:end]
    ppg = session.signals['ppg'][start:end]
    abp = session.signals['abp'][start:end]

    # build figure
    fig = generate_shared_xaxis_figure(ecg, ppg, abp, t)

    # overlay manual peaks
    row_map = {'ecg':1,'ppg':2,'abp':3}
    start_window = start/FS
    end_window = end/FS
    for sig, data in (annotations or {}).items():
        time_peaks = data.get('time_peak_positions', [])
        amps       = data.get('peak_amplitudes',       [])
        for idx, (x, y) in enumerate(zip(time_peaks, amps)):
            if  start_window <= x < end_window:
                fig.add_trace(go.Scatter(
                    x=[x], y=[y],
                    mode='markers',
                    marker_symbol='x', marker_size=10,
                    name=f"{sig} manual"
                ), row=row_map[sig], col=1)
    return fig

# 4) Quick debug panel
@app.callback(
    Output('metadata-display','children'),
    [ Input('annotations','data'),
      Input('current-window','data') ]
)
def debug_annotations(ann, widx):
    """
    ann: the annotations dict, e.g.
      {
        'ecg': {
          'sample_peak_positions': [...],
          'time_peak_positions':   [...],
          'peak_amplitudes':        [...],
          'windows':                [...],
          # …any other keys…
        },
        'ppg': { … },
        'abp': { … }
      }
    widx: zero-based window index
    """
    window_lo_sample = widx * WIN_SAMPLES
    window_hi_sample = (widx + 1) * WIN_SAMPLES
    window_lo_time   = widx * WIN_LEN_SEC
    window_hi_time   = (widx + 1) * WIN_LEN_SEC

    out = {
        "window_index": widx,
        "signals": {}
    }

    for sig, data in (ann or {}).items():
        sig_out = {}
        for key, vals in data.items():
            if not isinstance(vals, list):
                # not a list? just copy it over
                sig_out[key] = vals
                continue

            # numeric list → try to filter by window
            filtered = []
            if 'sample' in key:
                # interpret values as sample indices
                filtered = [v for v in vals
                            if window_lo_sample <= v < window_hi_sample]
            elif 'time' in key:
                # interpret values as time stamps
                filtered = [v for v in vals
                            if window_lo_time   <= v < window_hi_time]
            else:
                # unknown numeric list — leave unfiltered
                filtered = vals

            sig_out[key] = filtered

        out["signals"][sig] = sig_out

    return html.Pre(json.dumps(out, indent=2))