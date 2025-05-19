# CardioAnnotator

Interactive Django + Plotly Dash application for annotating physiological waveforms (ECG, PPG, ABP) stored in HDF5.

### Example:
![image](https://github.com/user-attachments/assets/5c6f960c-6cfe-47f5-800f-ff51e3cd92a2)

##  Features
- **Data Loading & Transformation**: Efficiently retrieves subject metadata and fixed‐length waveform windows from HDF5 (`.h5`) files.  
- **Multi-Signal Visualization**: Shared‐x‐axis Plotly subplots for ECG, PPG, and ABP with click‐to‐annotate markers.  
- **Interactive Annotation**: Add/remove peak annotations, clear all, and label windows via UI controls.  
- **Caching & Performance**: Client- and server-side caching of window slices to minimize I/O and speed up navigation.  
- **Extensible Framework**: Modular utilities for loading, serialization, plotting, and callbacks—easy to extend for new signals or metrics.

## Installation
### Prerequisites
- Python 3.11+  
- Conda (Miniconda or Anaconda)

### Clone & Setup

1. Clone repository
```bash
git clone https://github.com/ShayanRiyaz/CardioAnnotator.git
cd CardioAnnotator/analysis_dashboard
```

2. Create Conda environment
```bash
conda env create --file environment.yml
conda activate cardio_annotator
```

3. Apply Django migrations
```bash
python manage.py migrate
```
4. (Optional) Load sample data
- Place your HDF5 file at `data/raw/mimic3_data/mimic3_data_2_1.h5`

5. Run the development server
```bash
python manage.py runserver
```

## Usage
- **Select** Subject: Choose a subject from the dropdown and click **Load Subject**. The first 30-second window will cache and display.
- **Navigate Windows**: Use Previous, Next, or enter seconds in the **Jump To** field and click **Go**.
- **Add/Remove Peaks**: Toggle between **Add** and **Remove** mode, then click on waveform traces to annotate peaks.
- **Clear Annotations**: Click **Clear All** to remove peaks in the current window.
- **Label Windows**: Choose a label from the dropdown and click **Add Label** to tag the current window.
- ~~**Save Annotations**: Click **Save** to POST all annotations to the backend (stubbed—you can extend to persist to file or DB).~~

## Configuration
- **HDF5 Path**: Set H5_PATH in settings.py to point to your .h5 file.
- **Window Parameters**: Adjust WIN_LEN_SEC, WIN_SAMPLES, and NUM_WINDOWS in settings.py to match your dataset.
~~- **Static Files**: Place Django template helpers under static/annotations/js and Dash assets under assets/.~~

## Shortcomings & Future Work
- **Performance bottlenecks**: Each annotation click still triggers a full server‑side redraw and HDF5 file open. I plan to experiment with clientside callbacks or caching strategies to reduce latency.
- **Asset pipeline complexity**: Managing separate Django and Dash static folders has been cumbersome. I’m considering a unified build (e.g., React or a front‑end bundler) to streamline development.
- **No CI/CD or linting**: Right now there’s no continuous integration or formatting enforcement. I’ll set up GitHub Actions and pre‑commit hooks (e.g., black, flake8) to maintain code quality.

## Proposed Fixed Schema
```json
{
  "fix": {
    "subj_id": "<string>",
    "rec_id": "<string>",
    "files": "<string>",
    "af_status": "<int>",
    "subject_notes": "<any>"
  },
  "ppg": {
    "v":       "<number[]>",
    "fs":      "<int>",
    "method":  "<string>",
    "label":   "<string>"
  },
  "ekg": {
    "v":       "<number[]>",
    "fs":      "<int>",
    "method":  "<string>",
    "label":   "<string>"
  },
  "bp": {
    "v":       "<number[]>",
    "fs":      "<int>",
    "method":  "<string>",
    "label":   "<string>"
  }
}
```

## Contribution & License
Issues: use GitHub Issues for bugs or feature requests.
License: MIT © Shayan Riyaz