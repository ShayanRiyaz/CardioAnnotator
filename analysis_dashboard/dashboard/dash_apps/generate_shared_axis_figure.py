import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots



def generate_shared_xaxis_figure(y_ecg, y_ppg, y_abp, t):
    X_AXES_FONT_SIZE = Y_AXES_FONT_SIZE = 12
    X_AXIS_RANGE = [t[0],t[-1]+(t[1]-t[0])]
    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,  # Adjust vertical spacing between subplots
        subplot_titles=("Electro-Cardiogram (ECG)", "Photo-Plethysmography (PPG)", "Arterial Blood Pressure (ABP)")
    )
    
    fig.add_trace(go.Scatter(x=t, y=y_ecg,mode='lines+markers', marker=dict(size=6, opacity=0), meta={'signal': 'ecg'},customdata=[{'signal':'ecg'}]*len(t), name='ecg-base',hovertemplate='Time: %{x:.3f}s<br>Value: %{y:.3f}<extra></extra>',
                             ), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=y_ppg,mode='lines+markers', marker=dict(size=6, opacity=0), meta={'signal': 'ppg'},customdata=[{'signal':'ppg'}]*len(t), name='ppg-base',hovertemplate='Time: %{x:.3f}s<br>Value: %{y:.3f}<extra></extra>',
                             ), row=2, col=1)
    fig.add_trace(go.Scatter(x=t, y=y_abp,mode='lines+markers', marker=dict(size=6, opacity=0), meta={'signal': 'abp'},customdata=[{'signal':'abp'}]*len(t), name='abp-base',hovertemplate='Time: %{x:.3f}s<br>Value: %{y:.3f}<extra></extra>',
                             ), row=3, col=1) # , mode="lines+markers",marker=dict(opacity=1),line=dict(width=1)


    for i, title in enumerate(["Electro-Cardiogram (ECG)", "Photo-Plethysmography (PPG)", "Arterial Blood Pressure (ABP)"]):
        fig.layout.annotations[i].update(x=0.01, xanchor='left', font_size=12)

    fig.update_xaxes(dtick=0.4, row=1, col=1,range=X_AXIS_RANGE,
                     minor = dict(dtick=0.04,showgrid=True, gridcolor='lightgrey', gridwidth=0.5),
                     showticklabels=False,showgrid=True,gridcolor='grey',gridwidth=1)
    fig.update_xaxes(showticklabels=False, row=2, col=1,range=X_AXIS_RANGE)
    fig.update_xaxes(title_text="Time (s)", row=3, col=1,range=X_AXIS_RANGE) 

    fig.update_yaxes(title_text="mV", row=1, col=1, title_font_size=Y_AXES_FONT_SIZE, tickfont_size=Y_AXES_FONT_SIZE, 
                    dtick=0.1, showgrid=True, gridcolor='lightgrey', gridwidth=1, zeroline=False,automargin=True, tickmode='array',
    tickvals=np.arange(-1,1,0.25))
    fig.update_yaxes(title_text="test", row=2, col=1, title_font_size=Y_AXES_FONT_SIZE, tickfont_size=Y_AXES_FONT_SIZE,automargin=True)
    fig.update_yaxes(title_text="mmHg", row=3, col=1, title_font_size=Y_AXES_FONT_SIZE, tickfont_size=Y_AXES_FONT_SIZE,automargin=True)

    fig.update_layout(
        clickmode='event+select',
        height=800, 
        showlegend=False, 
        margin=dict(l=None,r=10,t=30,b=None), 
    )

    return fig