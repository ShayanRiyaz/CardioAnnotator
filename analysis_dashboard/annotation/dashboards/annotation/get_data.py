
import numpy as np
from types import SimpleNamespace
import h5py
import plotly.graph_objects as go
# --- Dummy session generation -----------------------------------------------

FS = 125                    # sampling rate
MINUTES = 30
DURATION_SEC = MINUTES * 60     # 30 minutes
TOTAL_SAMPLES = DURATION_SEC * FS
# Constants for windowing
WIN_LEN_SEC = 10          # seconds per window
WIN_SAMPLES = WIN_LEN_SEC * FS
NUM_WINDOWS = 180         # total windows (adjust based on data length


H5_PATH = "../data/raw/mimic3_data/mimic3_data_2_1.h5"  # Adjust this as needed
def get_subject_ids(h5_path=H5_PATH):
    with h5py.File(h5_path, 'r') as f:
        return list(f['subjects'].keys())

def load_subject_metadata(subj_id, h5_path=H5_PATH):
    """Load only subject metadata and signal info (not full waveform)."""
    def decode_bytes(val):
        if isinstance(val, (bytes, np.bytes_)):
            return val.decode('utf-8', errors='ignore')
        return val

    def load_group(g):
        out = {}
        for k in g.keys():
            val = g[k][()]
            # Fix for subject_notes: single-object array with bytes
            if isinstance(val, np.ndarray) and val.dtype == object and val.size == 1:
                val = decode_bytes(val[0])
            elif isinstance(val, (bytes, np.bytes_)):
                val = decode_bytes(val)
            out[k] = val
        return out

    with h5py.File(h5_path, 'r') as f:
        subject_group = f['subjects'][subj_id]
        return {
            'fix': load_group(subject_group['fix']),
            'ppg': load_group(subject_group['ppg']),
            'ecg': load_group(subject_group['ekg']),
            'bp':  load_group(subject_group['bp']),
        }

def load_window_slice(subj_id, widx, h5_path=H5_PATH):
    """Load a specific window slice of waveform data."""
    with h5py.File(h5_path, 'r') as f:
        subj = f['subjects'][subj_id]
        fs = subj['ppg']['fs'][()]
        start = widx * WIN_SAMPLES
        end = start + WIN_SAMPLES

        return {
            "start": start,
            "end": end,
            "fs": fs,
            "ppg": subj["ppg"]["v"][start:end][()].astype(np.float32).tolist(),
            "ecg": subj["ekg"]["v"][start:end][()].astype(np.float32).tolist(),
            "bp":  subj["bp"]["v"][start:end][()].astype(np.float32).tolist(),
            "t":   (np.arange(start, end) / fs).astype(np.float32).tolist(),
        }


# def get_subject_ids(h5_path=H5_PATH):
#     with h5py.File(h5_path, 'r') as f:
#         return list(f['subjects'].keys())

# def load_subject(subj_id, h5_path=H5_PATH):
#     with h5py.File(h5_path, 'r') as f:
#         subject_group = f['subjects'][subj_id]

#         def load_group(g):
#             return {
#                 k: g[k][()].decode('utf-8') if isinstance(g[k][()], bytes) else g[k][()]
#                 for k in g.keys()
#             }

#         return {
#             'fix': load_group(subject_group['fix']),
#             'ppg': load_group(subject_group['ppg']),
#             'ekg': load_group(subject_group['ekg']),
#             'bp':  load_group(subject_group['bp']),
#         }
    
# _loaded_subjects = {}  # In-memory cache

# def get_subject(subj_id, h5_path=H5_PATH):
#     if subj_id not in _loaded_subjects:
#         _loaded_subjects[subj_id] = load_subject(subj_id, h5_path)
#     return _loaded_subjects[subj_id]


# def load_window(subj_id, widx, h5_path=H5_PATH):
#     with h5py.File(h5_path, 'r') as f:
#         subj = f['subjects'][subj_id]
#         start = widx * WIN_SAMPLES
#         end = start + WIN_SAMPLES
#         return {
#             "ppg": subj["ppg"]["v"][start:end][()],
#             "ekg": subj["ekg"]["v"][start:end][()],
#             "bp":  subj["bp"]["v"][start:end][()],
#             "t":   np.arange(start, end) / subj["ppg"]["fs"][()],
#         }



def overlay_annotations(fig, annotations, subj_id, window_idx, fs, win_len_samples):
    """
    Adds peak annotations to a Plotly figure for the given subject window.

    Parameters:
        fig         : Plotly figure object
        annotations : dict of signal annotations
        subj_id     : current subject ID (optional, for logging/debugging)
        window_idx  : which window (zero-based)
        fs          : sampling rate
        win_len_samples : number of samples per window
    """
    peak_color_map = {'ecg': 'red', 'ppg': 'blue', 'abp': 'black'}
    row_map = {'ecg': 1, 'ppg': 2, 'abp': 3}

    start = window_idx * win_len_samples
    end = start + win_len_samples

    for sig, ann in (annotations or {}).items():
        if sig == 'window_label':
            continue
        samples = np.array(ann.get('sample_peak_positions', []), dtype=int)
        times = np.array(ann.get('time_peak_positions', []), dtype=float)

        # Mask down to current window
        mask = (samples >= start) & (samples < end)
        if not mask.any():
            continue

        win_samples = samples[mask]
        win_times = times[mask]

        x = win_times
        y = np.array([])

        try:
            trace = fig['data'][row_map[sig]-1]  # Access the base signal trace
            signal_y = trace['y']
            y = np.array([signal_y[int(s - start)] for s in win_samples])
        except Exception as e:
            print(f"[WARN] Could not align annotation for {sig} in window {window_idx}: {e}")
            continue
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode='markers',
            name=f"{sig}-manual-peaks",
            showlegend=False,
            marker=dict(symbol='x', size=10, color=peak_color_map[sig]),
            customdata=[{'signal': sig}] * len(x),
            hovertemplate='(%{x:.3f}, %{y:.3f})<extra></extra>'
        ), row=row_map[sig], col=1)

    return fig

def to_json_serializable(obj):
    if isinstance(obj, dict):
        return {str(k): to_json_serializable(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [to_json_serializable(v) for v in obj]

    elif isinstance(obj, np.ndarray):
        if obj.dtype == object:
            # Handle case: np.array([b'']) or np.array([b'note']) → string
            if len(obj) == 1 and isinstance(obj[0], (bytes, np.bytes_)):
                return obj[0].decode('utf-8', errors='ignore')
            # Handle general object arrays
            return [to_json_serializable(v) for v in obj.tolist()]
        else:
            return obj.astype(np.float32).tolist()

    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)

    elif isinstance(obj, (np.floating, np.float32, np.float64)):
        return float(obj)

    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)

    elif isinstance(obj, (bytes, np.bytes_)):
        return obj.decode('utf-8', errors='ignore')

    elif obj is None:
        return None

    elif isinstance(obj, str):
        return obj

    elif isinstance(obj, int): 
        return obj
    elif isinstance(obj, float): 
        return obj
        

    else:
        raise TypeError(f"Cannot serialize: {repr(obj)} of type {type(obj)}")