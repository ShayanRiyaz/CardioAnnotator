from dash import html, Input, Output, callback_context
from django_plotly_dash import DjangoDash

# Give it a unique name for django-plotly-dash
app_name_minimal = "MinimalDashTest"

minimal_app = DjangoDash(name=app_name_minimal)

minimal_app.layout = html.Div([
    html.Button("Click Me", id="minimal-button", n_clicks=0),
    html.Div(id="minimal-output")
])

@minimal_app.callback(
    Output("minimal-output", "children"),
    Input("minimal-button", "n_clicks"),
    prevent_initial_call=True
)
def minimal_test_callback(n_clicks):
    ctx = callback_context
    try:
        triggered_id = ctx.triggered_id
        return f"Button clicked! Triggered by: {triggered_id}. Clicks: {n_clicks}"
    except LookupError as e:
        # This is the error you're seeing
        return f"LookupError accessing callback_context: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# Then, make sure this minimal_app is registered and accessible in your Django views and templates.