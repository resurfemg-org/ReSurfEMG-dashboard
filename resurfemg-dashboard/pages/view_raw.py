"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

import dash
import dash_bootstrap_components as dbc
from dash import html


dash.register_page(__name__, path='/view-raw')


layout = html.Div([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1(id='emg-data-title', children='EMG data',
                        style={'text-align': 'center'}),
                html.Div(id='emg-filename'),
                dbc.Button('Remove data', id='emg-delete-button',
                           style={'background': 'red',
                                  'border': 'transparent'})
            ],
                id='emg-header',
                hidden=True,
                style={'align': 'center'}
            ),
            html.Div(id='emg-graphs-container',
                     className='six columns')
        ], width=6),

        dbc.Col([
            html.Div([
                html.H1(id='ventilator-data-title', children='Ventilator data',
                        style={'text-align': 'center'}),
                html.Div(id='ventilator-filename'),
                dbc.Button('Remove data', id='ventilator-delete-button',
                           style={'background': 'red',
                                  'border': 'transparent'})
            ],
                id='ventilator-header', hidden=True
            ),
            html.Div(
                id='ventilator-graphs-container',
                className='six columns')
        ], width=6)
    ]),
    html.Div(id='hidden-div'),
    html.Div(id='sample-req-emg'),
    html.Div(id='sample-req-vent')
])
