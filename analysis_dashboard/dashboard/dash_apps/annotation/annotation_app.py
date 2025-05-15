from dash.dependencies import Input, Output, State
import dash
from dash import dcc, html,no_update
import dash_bootstrap_components as dbc
from django_plotly_dash import DjangoDash
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import json
import numpy as np
from types import SimpleNamespace

from .annotation_layout import serve_layout
from ..generate_shared_axis_figure import generate_shared_xaxis_figure
from ..get_data import FS, WIN_SAMPLES, NUM_WINDOWS,WIN_LEN_SEC,to_json_serializable,overlay_annotations,load_subject_metadata,load_window_slice
import h5py

# Init Dash app
app = DjangoDash("SignalAnnotator", external_stylesheets=[dbc.themes.BOOTSTRAP],serve_locally=False)
app.layout = serve_layout

initial_ann = {
    'ecg': {'sample_peak_positions': [],'time_peak_positions': [], 'windows': []},
    'ppg': {'sample_peak_positions': [],'time_peak_positions': [], 'windows': []},
    'abp': {'sample_peak_positions': [],'time_peak_positions': [], 'windows': []}
    }

@app.callback(
    Output('subject-metadata-cache', 'data'),
    Output('current-subject-id', 'data'),
    Input('load-subject-btn', 'n_clicks'),
    State('subject-dropdown', 'value'),
    State('subject-metadata-cache', 'data'),
    prevent_initial_call=True
)
def load_subject_metadata_callback(n_clicks, subj_id, metadata_cache):
    if not n_clicks or not subj_id:
        raise PreventUpdate

    if metadata_cache is None:
        metadata_cache = {}

    if subj_id in metadata_cache:
        return no_update, subj_id

    metadata = load_subject_metadata(subj_id)
    metadata = to_json_serializable(metadata)
    metadata_cache[subj_id] = metadata
    return metadata_cache, subj_id

# 1) Navigation stays the same
@app.callback(
    Output('current-window','data'),
    [Input('prev-window-btn','n_clicks_timestamp'),
     Input('next-window-btn','n_clicks_timestamp'),
     Input('jump-go-btn','n_clicks_timestamp')],
    [State('current-window','data'),
     State('jump-to-input','value')],prevent_initial_call=True
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
    current_idx = int((jump_sec * FS) // WIN_SAMPLES)
    return max(0, min(current_idx, NUM_WINDOWS - 1))



def modify_peak_logic(clickData, ann, window_idx, mode):
    """
    clickData   : the dict from dcc.Graph.clickData
    ann         : the existing annotations dict (may be {})
    window_idx  : zero‐based index of the current window
    mode        : 'add' or 'remove'
    returns     : a NEW annotations dict with the one peak added or removed
    """
    # 1) shallow-copy the top-level dict so we don't mutate in place
    new_ann = { sig: data.copy() for sig, data in (ann or {}).items() }

    # 2) unpack click info
    pt          = clickData['points'][0]

    try:
        sig = pt['customdata']['signal']          # 'ecg' / 'ppg' / 'abp'
    except (KeyError, TypeError, IndexError):
        raise PreventUpdate 
    t_rel       = pt['x']                             # seconds into this window
    local_idx   = pt['pointIndex']                    # 0…WIN_SAMPLES-1
    sample_idx  = window_idx * WIN_SAMPLES + local_idx

    # 3) make sure this signal has its lists in place
    sd          = new_ann.setdefault(sig, {})
    sp          = sd.setdefault('sample_peak_positions', [])
    tp          = sd.setdefault('time_peak_positions',   [])

    # 4) add or remove
    if mode == 'add':
        if sample_idx not in sp:
            sp.append(sample_idx)
            tp.append(t_rel)

    else:  # remove
        # drop any peak within ±1 sample of the click
        pairs = list(zip(sp, tp))
        kept  = [(s, t) for s, t in pairs if abs(s - sample_idx) > 1]
        if kept:
            sp[:], tp[:] = zip(*kept)
        else:
            sp.clear()
            tp.clear()

    # 5) re‐sort so everything stays in chronological order
    sorted_pairs = sorted(zip(sp, tp), key=lambda st: st[0])
    sp[:] = [s for s, _ in sorted_pairs]
    tp[:] = [t for _, t in sorted_pairs]

    new_ann[sig]['sample_peak_positions'] = sp
    new_ann[sig]['time_peak_positions']   = tp
    return new_ann

# 3) Redraw on window or annotation change
@app.callback(
    Output("signal-plots", "figure"),
    Input("current-window", "data"),
    Input("annotations", "data"),
    State("current-subject-id", "data"),
    
    prevent_initial_call=True
)
def update_plots(window_idx,annotations, subj_id):
    if (window_idx == 0) or subj_id is None:
        raise PreventUpdate
    
    window_data = load_window_slice(subj_id, window_idx)
    fs = window_data["fs"]
    t, ppg, ecg, abp = window_data["t"], window_data["ppg"], window_data["ekg"], window_data["bp"]

    fig = generate_shared_xaxis_figure(ecg, ppg, abp, t)
    fig = overlay_annotations(fig, annotations, subj_id, window_idx, fs, WIN_SAMPLES)
    return fig
# @app.callback(
#     Output("signal-plots", "figure"),
#     Input("current-window", "data"),
#     State("current-subject-id", "data"),
#     State("subject-metadata-cache", "data"),
#     State("annotations", "data"),
#     prevent_initial_call=True
# )
# def update_plot_from_slice(window_idx, subj_id, cache, annotations):
#     if subj_id is None or subj_id not in cache:
#         raise PreventUpdate

#     try:
#         win_data = load_window_slice(subj_id, window_idx)
#         meta = cache[subj_id]
#         fs = meta['ppg']['fs']
#         t = np.arange(len(win_data['ppg'])) / fs

#         fig = generate_shared_xaxis_figure(
#             win_data['ekg'], win_data['ppg'], win_data['bp'], t
#         )

#         # Overlay peaks
#         fig = overlay_annotations(fig, annotations, subj_id, window_idx, fs)

#         return fig
#     except Exception as e:
#         print(f"[ERROR] Failed to load slice for {subj_id}, window {window_idx}: {e}")
#         raise PreventUpdate
    
# @app.callback(
#     [Output("signal-plots", "figure")],
#     [Input("current-window", "data")],
#     [
#     State("annotations", "data"),
#     State("current-subject-id", "data"),
#     State("subject-data-cache", "data")
#     ],prevent_initial_call = True,
# )
# def update_plots(window_idx, annotations, current_subject_id, cache):
#     if not current_subject_id or current_subject_id not in cache:
#         raise PreventUpdate
#     # slice your real data
#     start = window_idx * WIN_SAMPLES
#     end   = start + WIN_SAMPLES
#     subject = cache[current_subject_id]
#     fs = subject["ppg"]["fs"]
#     ecg = subject["ekg"]["v"][start:end]
#     ppg = subject["ppg"]["v"][start:end]
#     abp = subject["bp"]["v"][start:end]
#     t   = np.arange(start, end) / fs


#     # build figure
#     fig = generate_shared_xaxis_figure(ecg, ppg, abp, t)
#     fig.data = [
#     tr for tr in fig.data
#     if not (isinstance(tr.uid, str) and tr.uid.endswith("-manual-"))]

#     peak_color_map = {'ecg':'red','ppg':'blue','abp':'black'}
#     row_map        = {'ecg':1,'ppg':2,'abp':3}

#     # vectorized overlay:
#     for sig, data in (annotations or {}).items():
#         # load lists into arrays
#         samples = np.array(data.get('sample_peak_positions', []), dtype=int)
#         times   = np.array(data.get('time_peak_positions',    []), dtype=float)

#         # mask down to the current window
#         mask  = (samples >= start) & (samples <  end)
#         if not mask.any():
#             continue

#         win_samples = samples[mask]
#         win_times   = times[mask]
#         # fetch y-values in one vectorized slice
#         y_vals      = subject[sig]['v'][win_samples]

#         # add a single scatter trace for all peaks of this signal
#         fig.add_trace(
#             go.Scatter(x=win_times,y=y_vals,
#                 mode='markers',name=f"{sig}-manual-{win_samples}",showlegend=False,
#                 marker=dict(
#                     symbol='x',
#                     size=10,
#                     color=peak_color_map[sig]
#                 ),
#             ),
#             row=row_map[sig], col=1)

#     return fig


@app.callback(
    Output('annotations', 'data'),
    Output('signal-plots', 'clickData'),
    [
      Input('signal-plots',  'clickData'),
      Input('clear-all-btn', 'n_clicks')
    ],
    [
      State('mode-selector',  'value'),
      State('annotations',     'data'),
      State('current-window',  'data')
    ],
    prevent_initial_call=True
)
def modify_annotations(clickData, clear_n, mode, ann, window_idx):
    # 1) Figure out what fired us
    new_ann = { sig: data.copy() for sig, data in (ann or {}).items() }


    if clickData:
        return modify_peak_logic(clickData, new_ann, window_idx, mode), None

    elif clear_n:
        # 2) Start from the existing store (or empty template)
        new_ann = ann.copy() if isinstance(ann, dict) else initial_ann.copy()
        # only clear this window’s peaks
        start, end = window_idx*WIN_SAMPLES, (window_idx+1)*WIN_SAMPLES
        for sig, data in new_ann.items():
            sp = data.get('sample_peak_positions', [])
            tp = data.get('time_peak_positions',    [])
            kept = [(s,t) for s,t in zip(sp,tp) if not (start <= s < end)]
            if kept:
                s_kept, t_kept = map(list, zip(*kept))
            else:
                s_kept, t_kept = [], []
            new_ann[sig]['sample_peak_positions'] = s_kept
            new_ann[sig]['time_peak_positions']   = t_kept
        return new_ann, None
    
    else:
        raise PreventUpdate
    
        # nothing relevant clicked
   






@app.callback(
    Output('metadata-display','children'),
    [ Input('annotations','data'),
      Input('current-window','data') ],prevent_initial_call=True,
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