from dash import html, dcc
import dash_bootstrap_components as dbc
from .dummy_data import generate_shared_axis_figure
import numpy as np
from .config import WIN_LEN_SEC, FS, WIN_SAMPLES,NUM_WINDOWS

# Style for the single dcc.Graph component
# It should fill its container.
single_graph_style = {
    'height': '100%', # Take full height of its parent (the dbc.Col)
    'width': '100%',
    'padding':'0'
}

# Column style for the plots
plots_column_style = {
    'height': '100%', # This should resolve to 100vh from parent Row
    'gridGrow': 1, # This is a grid column, so it should take the full height of the row
    'gridShrink': 1, # This is a grid column, so it should take the full height of the row
    'display': 'flex',       # Use flex to make dcc.Graph fill it
    'flexDirection': 'row', # (though with one child, not strictly necessary for distribution)
    'padding': '0',          # No internal padding in the column
    'margin': '0'
}

def serve_layout():
    zeros = np.zeros(WIN_SAMPLES)
    initial_fig = generate_shared_axis_figure(zeros, zeros, zeros, zeros)
    return dbc.Container([
        dcc.Store(id='current-window', data=0),
        dcc.Store(id='annotations',   data={}),
        dbc.Row([
                html.H1("Annotation Dashboard", style={'textAlign': 'center'}),
                html.Hr(),
                html.P("This is a placeholder for the ECG, PPG, and ABP signals."),
                html.P("Use the buttons to add/remove peaks and label the window."),
        ], style={'height': '100%',
                'padding': '0',
                'margin': '0',
                'textAlign':'center'}),
        html.Hr(),
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
                html.Button("Add Peak", id='add-peak-btn', className='mb-2 me-1'),
                html.Button("Remove Peak", id='remove-peak-btn', className='mb-2'),
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
                    html.Button("Prev Window", id='prev-window-btn', className='me-2'),
                    html.Button("Next Window", id='next-window-btn')
                ], className='mt-3'),
                html.Hr(),
                html.H5("Jump to Time (s)"),
                dcc.Input(id='jump-to-input', type='number', value=0, min=0),
                html.Button("Go", id='jump-go-btn', className='ms-2')
            ], width=3, style={'height': '80vh'})
        ], className='my-2'),
        dbc.Row([
            dbc.Col(html.Div(id='metadata-display', children="Metadata will appear here"), width=12),
            dbc.Col(html.Button("Save Annotations", id='save-btn', className='float-end'), width=12)
        ])
    ], fluid=True, style={'height': '100%', 'padding': '0', 'margin': '0'})