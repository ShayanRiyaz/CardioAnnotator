
import numpy as np
from types import SimpleNamespace

# --- Dummy session generation -----------------------------------------------

FS = 125                    # sampling rate
DURATION_SEC = 30 * 60     # 30 minutes
TOTAL_SAMPLES = DURATION_SEC * FS
# Constants for windowing
WIN_LEN_SEC = 10          # seconds per window
WIN_SAMPLES = WIN_LEN_SEC * FS
NUM_WINDOWS = 180         # total windows (adjust based on data length)

t_full = np.arange(TOTAL_SAMPLES) / FS

# Synthetic signals:
ecg_full = 0.5 * np.sin(2 * np.pi * 1.2 * t_full) \
           + 0.05 * np.random.randn(TOTAL_SAMPLES)
ppg_full = 0.8 * np.cos(2 * np.pi * 1.0 * t_full) \
           + 0.02 * np.random.randn(TOTAL_SAMPLES)
abp_full = 0.6 * np.sin(2 * np.pi * 1.1 * t_full + 0.5) \
           + 0.03 * np.random.randn(TOTAL_SAMPLES)

# Fake PPG-peak predictions every ~1 s:
ppg_peaks = list(np.where(np.diff(np.signbit(np.diff(ppg_full))) < 0)[0] + 1)

# Build a SimpleNamespace to mimic your real session
session = SimpleNamespace(
    fs=FS,
    signals={
        't':t_full,
        'ecg': ecg_full,
        'ppg': ppg_full,
        'abp': abp_full,
    },
    predictions={
        'ppg_peaks': ppg_peaks
    }
)