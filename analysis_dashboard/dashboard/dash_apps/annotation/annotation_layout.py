from dash import html, dcc
import dash_bootstrap_components as dbc
from ..generate_shared_axis_figure import generate_shared_xaxis_figure
import numpy as np
from ..get_data import WIN_SAMPLES

# Style for the single dcc.Graph component
# It should fill its container.

title_row_style = {
        'paddingTop': '0.25rem',
        'paddingBottom': '0.25rem',
        'margin': '0',       # remove any extra outer margin
        'textAlign': 'center',  # Center the title      
        # 'backgroundColor': '#f8f9fa',  # Light grey background
        # 'borderBottom': '1px solid #dee2e6',  # Light border at the bottom
        # 'borderTop': '1px solid #dee2e6',  # Light border at the top
        # 'borderRadius': '0.25rem',  # Rounded corners
        # 'boxShadow': '0 1px 3px rgba(0, 0, 0, 0.1)'  # Subtle shadow

    }


single_graph_style = {
    'height': '100%', # Take full height of its parent (the dbc.Col)
    'width': '100%',
    'padding':'0'
}

# Column style for the plots
plots_column_style = {
    'height': '60%',       # This should resolve to 100vh from parent Row
    'gridGrow': 1,          # This is a grid column, so it should take the full height of the row
    'gridShrink': 1,        # This is a grid column, so it should take the full height of the row
    'display': 'flex',      # Use flex to make dcc.Graph fill it
    'flexDirection': 'row', # (though with one child, not strictly necessary for distribution)
    'padding': '0',         # No internal padding in the column
    'margin': '0'
}

def serve_layout():
    zeros = np.zeros(WIN_SAMPLES)
    initial_fig = generate_shared_xaxis_figure(zeros, zeros, zeros, zeros)
    initial_ann = {
    'ecg': {'sample_peak_positions': [],'time_peak_positions': [],'peak_amplitudes': [], 'windows': []},
    'ppg': {'sample_peak_positions': [],'time_peak_positions': [],'peak_amplitudes': [], 'windows': []},
    'abp': {'sample_peak_positions': [],'time_peak_positions': [],'peak_amplitudes': [], 'windows': []}
    }
    return dbc.Container([
        dcc.Store(id='current-window', data=0),
        dcc.Store(id='annotations', data=initial_ann),
        
        dbc.Row([
                html.H1(
                    "Annotation Dashboard",
                    style={
                        'marginTop': '0',    # kill default H1 top margin
                        'marginBottom': '0', # kill default H1 bottom margin
                        'fontSize': '1.5rem' # you can also shrink the font
                    }
                ),
                html.Hr(style={'margin': '0.25rem 0'}),
                html.P(
                    "This is a placeholder for the ECG, PPG, and ABP signals.",
                    style={'margin': '0'}
                ),
                html.P(
                    "Use the buttons to add/remove peaks and label the window.",
                    style={'margin': '0', 'marginBottom': '0.25rem'}
                ),
            ],
            style=title_row_style,
            className='text-center g-0'  # g-0 removes gutter
        ),
        # thin separator
        html.Hr(style={'margin': '0.5rem 0'}),

        dbc.Row([

            dbc.Col([
                    dcc.Graph(
                        id='signal-plots', # Single ID for the graph component
                        figure=initial_fig,
                        style=single_graph_style,
                        config={'responsive': True} # Ensure it resizes with container
                    )], md=9, style=plots_column_style),

                dbc.Col([
                    html.H5("Annotation Tools"),
                    dcc.RadioItems(
                    id='mode-selector',
                    options=[
                        {'label':'Add Peak',    'value':'add'},
                        {'label':'Remove Peak', 'value':'remove'},
                    ],
                    value='add',
                    inline=True
                    ),
                    html.Hr(),
                    html.H5("Window Label"),
                    dcc.Dropdown(
                        id='window-label-dropdown',
                        options=[
                            {'label': 'Clean', 'value': 'clean'},
                            {'label': 'Noisy', 'value': 'noisy'},
                            {'label': 'Motion', 'value': 'motion'}
                        ],
                        value='clean'
                    ),
                    html.Hr(),
                    html.Div([
                        html.Button("Prev Window", id='prev-window-btn', n_clicks_timestamp=0, className='me-1'),
                        html.Button("Next Window", id='next-window-btn',n_clicks_timestamp=0)
                    ], className='mb-3'),
                    html.Hr(),
                    html.H5("Jump to Time (s)"),
                    dcc.Input(id='jump-to-input', type='number', value=0, min=0),
                    html.Button("Go", id='jump-go-btn', className='ms-2')
                ], width=3, style={'height': '60%'})
            ], className='my-2'),

        dbc.Row([
            dbc.Col(html.Div(id='metadata-display', children="Metadata will appear here"), width=12),
            dbc.Col(html.Button("Save Annotations", id='save-btn', className='float-end'), width=12)
        ], style={'height': '60%'}),


        ], fluid=True, style={'height': '50%', 'padding': '0', 'margin': '0'})