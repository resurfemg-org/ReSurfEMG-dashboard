from dash import Dash
import dash_bootstrap_components as dbc
import static_variables

variables = static_variables.get_singleton()
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.13.0/css/all.css"
external_stylesheets = [dbc.themes.BOOTSTRAP, FONT_AWESOME]
app = Dash(__name__,
           use_pages=True,
           external_stylesheets=external_stylesheets,
           suppress_callback_exceptions=True)
