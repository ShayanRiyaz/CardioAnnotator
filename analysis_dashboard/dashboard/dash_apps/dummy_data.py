import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots

def generate_shared_axis_figure(y_ecg, y_ppg, y_abp, t):
    # Create a figure with 3 rows, 1 column, and shared x-axes
    # t = np.arange(y_ecg.size) / fs
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,  # Adjust vertical spacing between subplots
        subplot_titles=("Electro-Cardiogram (ECG)", "Photo-Plethysmography (PPG)", "Arterial Blood Pressure (ABP)")
    )

    fig.add_trace(go.Scatter(x=t, y=y_ecg, name="ECG"), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=y_ppg, name="PPG"), row=2, col=1)
    fig.add_trace(go.Scatter(x=t, y=y_abp, name="ABP"), row=3, col=1)

    fig.update_layout(

        xaxis=dict(range=[t[0], t[-1]], fixedrange=False),  
        xaxis2=dict(range=[t[0], t[-1]], fixedrange=False), 
        xaxis3=dict(range=[t[0], t[-1]], fixedrange=False), 
        height=None, 
        showlegend=False, 
        margin=dict(l=10,r=10,t=30,b=10), 
    )

    # Customize subplot titles if needed (alternative to annotations)
    for i, title in enumerate(["Electro-Cardiogram (ECG)", "Photo-Plethysmography (PPG)", "Arterial Blood Pressure (ABP)"]):
        fig.layout.annotations[i].update(x=0.01, xanchor='left', font_size=12)
    fig.update_xaxes(showticklabels=False, row=1, col=1)
    fig.update_xaxes(showticklabels=False, row=2, col=1)
    fig.update_xaxes(title_text="Time (s)", row=3, col=1) # Add title to the shared x-axis
    fig.update_yaxes(title_text="ECG", row=1, col=1, title_font_size=10, tickfont_size=10)
    fig.update_yaxes(title_text="PPG", row=2, col=1, title_font_size=10, tickfont_size=10)
    fig.update_yaxes(title_text="ABP", row=3, col=1, title_font_size=10, tickfont_size=10)

    return fig