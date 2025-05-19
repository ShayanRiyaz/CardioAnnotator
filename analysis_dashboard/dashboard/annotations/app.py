import dash, json, os
from dash.dependencies import Input, Output, State
from dash import html,no_update
import dash_bootstrap_components as dbc
from django_plotly_dash import DjangoDash
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

from .layout import serve_layout,initial_ann
from .utils.generate_shared_axis_figure import generate_shared_xaxis_figure
from .utils.get_data import FS, WIN_SAMPLES, NUM_WINDOWS,WIN_LEN_SEC,to_json_serializable,overlay_annotations,load_subject_metadata,load_window_slice

ASSETS_PATH = os.path.join(
    os.path.dirname(__file__),
    '..', 'dash_apps', 'annotation', 'assets'
)
app = DjangoDash("SignalAnnotator", external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],serve_locally=False)
app.layout = serve_layout



@app.callback(
    Output('subject-metadata-cache', 'data'),
    Output('current-subject-id', 'data'),
    Output('current-window', 'data'),
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

    # Check if window 0 data for this subject is already cached
    if subj_id in metadata_cache and \
       'windows' in metadata_cache[subj_id] and \
       0 in metadata_cache[subj_id]['windows']:
        # If already cached, just update current subject and don't modify cache or trigger reset
        return no_update, subj_id,0

    # Ensure the subject entry and 'windows' dictionary exist
    if subj_id not in metadata_cache:
        metadata_cache[subj_id] = {}
    if 'windows' not in metadata_cache[subj_id]:
        metadata_cache[subj_id]['windows'] = {}

    # Load data for window 0
    window_0_data = load_window_slice(subj_id, 0)
    serializable_window_0_data = to_json_serializable(window_0_data)

    # Store window 0 data in the cache
    metadata_cache[subj_id]['windows'][0] = serializable_window_0_data

    return metadata_cache, subj_id,0










# 1) Navigation stays the same
@app.callback(
    Output('current-window','data',allow_duplicate=True),
    [Input('prev-window-btn','n_clicks_timestamp'),
     
     Input('next-window-btn','n_clicks_timestamp'),
     Input('jump-go-btn','n_clicks_timestamp')],
     Input('load-subject-btn', 'n_clicks'),
     
    [State('current-window','data'),
     State('jump-to-input','value')],prevent_initial_call=True
)
def navigate(prev_ts, next_ts, go_ts,load_subject_check, current_idx, jump_sec):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id']
    if trigger_id == 'load-subject-btn.n_clicks':
        return min(current_idx + 1, NUM_WINDOWS - 1)
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










# 3) Redraw on window or annotation change
@app.callback(
    Output("signal-plots", "figure"),
    [
    Input("current-window", "data"),
    Input("annotations", "data"),
    ],
    [
    State("current-subject-id", "data"),
    ],
    prevent_initial_call=True
)
def update_plots(window_idx,annotations, subj_id):
    if (window_idx is None) or subj_id is None:
        raise PreventUpdate
    
    window_data = load_window_slice(subj_id, window_idx)
    fs = window_data["fs"]
    t, ppg, ecg, abp = window_data["t"], window_data["ppg"], window_data["ecg"], window_data["bp"]

    fig = generate_shared_xaxis_figure(ecg, ppg, abp, t)
    fig = overlay_annotations(fig, annotations, subj_id, window_idx, FS, WIN_SAMPLES)
    
    return fig









@app.callback(
    Output('annotations', 'data'),
    Output('signal-plots', 'clickData'),
    [
      Input('signal-plots',  'clickData'),
      Input('clear-all-btn', 'n_clicks'),
      Input('load-subject-btn', 'n_clicks'),
      Input('add-label-btn',  'n_clicks'),
    ],
    [
      State('mode-selector',  'value'),
      State('annotations',     'data'),
      State('current-window',  'data'),
      State('window-label-dropdown', 'value'),

    ],
    prevent_initial_call=True
)
def modify_annotations(clickData, clear_all_clicked,load_subject_clicked,add_label_button_clicked,mode, ann, window_idx,label_value):
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id']
    if trigger_id is None:
        raise PreventUpdate
    
    if trigger_id == 'add-label-btn.n_clicks':
        ann = ann.copy()
        # Overwrite the single-string label
        ann['window_label'] = label_value
        return ann, None

    if trigger_id == 'load-subject-btn.n_clicks':
        return initial_ann.copy(), None
        
    # # 1) Figure out what fired us
    new_ann = {
    sig: (data.copy() if isinstance(data, dict) else data)
    for sig, data in (ann or {}).items()
    }

    if trigger_id == 'signal-plots.clickData':
        return modify_peak_logic(clickData, new_ann, window_idx, mode), None

    elif trigger_id == 'clear-all-btn.n_clicks':
        # 2) Start from the existing store (or empty template)
        base = ann.copy() if isinstance(ann, dict) else initial_ann.copy()

        # 2) now shallow-copy only the dict‐valued entries
        new_ann = {
            key: (val.copy() if isinstance(val, dict) else val)
            for key, val in base.items()
        }
        # only clear this window’s peaks
        start, end = window_idx*WIN_SAMPLES, (window_idx+1)*WIN_SAMPLES
        for sig, data in new_ann.items():
            if sig == 'window_label': continue
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
    







def modify_peak_logic(clickData, ann, window_idx, mode):
    """
    Input:
        clickData   : the dict from dcc.Graph.clickData
        ann         : the existing annotations dict (may be {})
        window_idx  : zero‐based index of the current window
        mode        : 'add' or 'remove'
    
    Output:
        returns     : a NEW annotations dict with the one peak added or removed
    """
    # 1) shallow-copy the top-level dict so we don't mutate in place
    new_ann = {
    sig: (data.copy() if isinstance(data, dict) else data)
    for sig, data in (ann or {}).items()
    }
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



# @app.callback(
#     Output('signal-plots', 'figure'),
#     Input('crosshair-toggle', 'value'),
#     State('signal-plots', 'figure'),
#     prevent_initial_call=True
# )
# def toggle_crosshair(toggle, fig):
#     ctx = dash.callback_context
#     trigger_id = ctx.triggered[0]['prop_id']
#     if trigger_id != 'crosshair-toggle.value':
#         return None
#     enabled = 'enabled' in toggle  # or whatever value you used
#     # Flip showspikes on every xaxis in the layout
#     for ax in list(fig.get('layout', {})):
#         if ax.startswith('xaxis'):
#             fig['layout'][ax]['showspikes'] = enabled
#     return fig




@app.callback(
    Output('metadata-display','children'),
    [Input('annotations','data'),
      Input('current-window','data'),
      ],
    prevent_initial_call=True,
)
def debug_annotations(ann, widx):
    if ann is None or widx is None:
        raise PreventUpdate

    # window bounds (in samples & seconds)
    window_lo_sample = widx * WIN_SAMPLES
    window_hi_sample = (widx + 1) * WIN_SAMPLES
    window_lo_time   = widx * WIN_LEN_SEC
    window_hi_time   = (widx + 1) * WIN_LEN_SEC

    # start building our output
    out = {
        "window_index": widx,
        "window_label": ann.get('window_label', ""),
        "signals": {}
    }
    # 2) now filter each signal’s lists by the window bounds
    for sig, data in (ann or {}).items():
        # skip the top‐level window_label entry
        if sig == 'window_label':
            continue
        sig_out = {}
        for key, vals in data.items():
            # pass through any non-list values
            if not isinstance(vals, list):
                sig_out[key] = vals
                continue
            if 'sample' in key:
                sig_out[key] = [v for v in vals if window_lo_sample <= v < window_hi_sample]
            elif 'time' in key:
                sig_out[key] = [v for v in vals if window_lo_time   <= v < window_hi_time]
            else:
                sig_out[key] = vals
        out["signals"][sig] = sig_out
    return html.Pre(json.dumps(out, indent=2))
