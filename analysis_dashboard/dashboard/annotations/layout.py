from dash import html, dcc
import dash_bootstrap_components as dbc
from .utils.generate_shared_axis_figure import generate_shared_xaxis_figure
import numpy as np
from .utils.get_data import WIN_SAMPLES,get_subject_ids

subject_options = [{"label": sid, "value": sid} for sid in get_subject_ids()]
initial_ann = {'window_label': "",
    'ecg': {'sample_peak_positions': [],'time_peak_positions': []},
    'ppg': {'sample_peak_positions': [],'time_peak_positions': []},
    'abp': {'sample_peak_positions': [],'time_peak_positions': []}
    }

title_row_style = {
        'paddingTop': '0.25rem',
        'paddingBottom': '0.25rem',
        'margin': '0',       # remove any extra outer margin
        'textAlign': 'center',  # Center the title      
    }


single_graph_style = {
    'height': '100%', # Take full height of its parent (the dbc.Col)
    'width': '100%',
    'padding':'0'
}

# Column style for the plots
plots_column_style = {
    'height': '75%',       # This should resolve to 100vh from parent Row
    'gridGrow': 1,          # This is a grid column, so it should take the full height of the row
    'gridShrink': 1,        # This is a grid column, so it should take the full height of the row
    'display': 'flex',      # Use flex to make dcc.Graph fill it
    'flexDirection': 'row', # (though with one child, not strictly necessary for distribution)
    'padding': '0',         # No internal padding in the column
    'margin': '0'
}


zeros = np.zeros(WIN_SAMPLES)
initial_fig = generate_shared_xaxis_figure(zeros, zeros, zeros, zeros)
def serve_layout():
    return dbc.Container([
        dcc.Store(id='annotations', data=initial_ann),
        dcc.Store(id="reset-annotations-trigger"),
        dcc.Store(id="subject-data-cache"),
        dcc.Store(id='subject-metadata-cache', data={}),
        dcc.Store(id='current-subject-id', data=None),
        dcc.Store(id='current-window', data=-1),

        html.Div(id='signal-display-container'),
        dbc.Row([
                html.H1(
                    "Annotation Dashboard",
                    style={
                        'marginTop': '0',    # kill default H1 top margin
                        'marginBottom': '0', # kill default H1 bottom margin
                        'fontSize': '1.5rem' # you can also shrink the font
                    }
                ),
            ],
            style=title_row_style,
            className='text-center g-0'  # g-0 removes gutter
        ),
        html.Hr(style={'margin': '0.5rem 0'}),


        dbc.Row([
            # dbc.Col([dcc.Checklist(id='crosshair-toggle',
            #                       options=[{'label': 'Enable crosshair', 'value': 'enabled'}],
            #                       value=[],)],style={'height': '2%'},width=1),
            dbc.Col([
                    dcc.Graph(
                        id='signal-plots', # Single ID for the graph component
                        figure=initial_fig,
                        style=single_graph_style,
                        config={'responsive': True,
                                # 'editable': True,               # enable general editing
                                # 'edits': {'shapePosition': True},
                                },# allow moving shapes} # Ensure it resizes with container
                    )], md=9, style=plots_column_style),

            dbc.Col([
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        html.Label("Subject:"),
                        dcc.Dropdown(id='subject-dropdown',options=subject_options,placeholder='Select a subject'),
                        ]),
                    dbc.Col([dbc.Button('Load', id='load-subject-btn',active=False, n_clicks=0)]),
                    ]),

                    html.Hr(),
                    html.Div([
                        dbc.Button("Prev Window", id='prev-window-btn', n_clicks=0,n_clicks_timestamp=0, className='me-2'),
                        dbc.Button("Next Window", id='next-window-btn',n_clicks=0,n_clicks_timestamp=0)
                    ], className='me-3'),
                
                    html.Hr(),
                    
                    dbc.Row([
                        html.H5("Annotation Tools"),
                        dbc.Col([
                            dcc.RadioItems(id='mode-selector',
                                options=[
                                {'label':'Add Peak',    'value':'add'},
                                {'label':'Remove Peak', 'value':'remove'},],
                            value='add',inline=True),
                        ]),
                        dbc.Col([dbc.Button("Clear All Peaks", id="clear-all-btn", className="mt-2 btn-danger",n_clicks=0)]),
                    ]),

                    html.Hr(),
                    html.H5("Window Label"),
                    dbc.Row([
                        dbc.Col([
                            dcc.Dropdown(
                                id='window-label-dropdown',
                                options=[
                                    {'label': 'Clean', 'value': 'clean'},
                                    {'label': 'Noisy', 'value': 'noisy'},
                                    {'label': 'Motion', 'value': 'motion'}
                                ],
                                value='clean'),
                        ],width=9),
                        dbc.Col([dbc.Button("Add", id='add-label-btn',active=False,n_clicks=0,n_clicks_timestamp=0, className='me-1')],width=3),
                    ]),

                    html.Hr(),
                    html.H5("Jump to Time (s)"),
                    dbc.Row([
                        dbc.Col([dcc.Input(id='jump-to-input', type='number', value=0, min=0)],width=9),
                        dbc.Col([dbc.Button("Go", id='jump-go-btn', className='me-4')],width=3),
                    ]),
                    
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([dbc.Button("Save", id='save-btn', className='float-end')],style={'gridGrow': 1,'gridShrink': 1,'margin': '0.5l'}),
                        dbc.Col([dbc.Button("Export", id='export-btn', className='float-end')],style={'gridGrow': 1,'gridShrink': 1,'margin': '-0.5l'}),
                    ]),

                    html.Hr(),
                    dbc.Row([html.Div(id='metadata-display', children="Metadata will appear here")]),
                ], width=3, style={'height': '25%'})
            ], className='me-5'),


        ], fluid=True, style={'height': '50%', 'padding': '0', 'margin': '0'})


