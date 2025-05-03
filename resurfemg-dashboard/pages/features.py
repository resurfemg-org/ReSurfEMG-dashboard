"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
from definitions import (ComputedFeatures, BreathSelectionMethod,
                         default_breath_method)
from definitions import (EMG_FILENAME_FEATURES, FEATURES_COMPUTE_BTN,
                         FEATURES_EMG_GRAPH_DIV, FEATURES_DOWNLOAD_BTN,
                         FEATURES_DOWNLOAD_DCC, FEATURES_DOWNLOAD_TOOLTIP,
                         FEATURES_COMPUTE_TOOLTIP, FEATURES_LOADING,
                         LOAD_FEATURES_DIV, FEATURES_SELECT_LEAD,
                         FEATURES_SELECT_COMPUTATION, FEATURES_TABLE)


dash.register_page(__name__, path='/features')

select_lead_card = dbc.Card([
    dbc.CardHeader("Select the lead"),
    dbc.CardBody([
        dbc.Select(
            id=FEATURES_SELECT_LEAD,
            options=[
            ]
        )
    ])
])

select_computation_card = dbc.Card([
    dbc.CardHeader("Select the computation"),
    dbc.CardBody([
        dbc.Label("Breath identification method"),
        dbc.Select(
            id=FEATURES_SELECT_COMPUTATION,
            options=[
                {"label": "Variability",
                 "value": BreathSelectionMethod.VARIABILITY},
                {"label": "Shannon Entropy",
                 "value": BreathSelectionMethod.SHANNON_ENTROPY},
                {"label": "Fixed Sample Entropy",
                 "value": BreathSelectionMethod.SAMPLE_ENTROPY},
                {"label": "Logarithmic Remapping",
                 "value": BreathSelectionMethod.LOG_REMAPPING},
            ],
            value=default_breath_method
        )
    ])
])

layout = html.Div([
    html.P(),
    html.Div(id=EMG_FILENAME_FEATURES),
    html.Div(id=LOAD_FEATURES_DIV),
    dbc.Row([
        html.P(),
        dbc.Col([
            select_lead_card
        ], width=2),
        dbc.Col([
            html.Div(id=FEATURES_EMG_GRAPH_DIV)
        ], width=10)
    ]),
    dbc.Row([
        html.Div([
            html.Button(
                className="fas fa-play",
                id=FEATURES_COMPUTE_BTN,
                style={'color': 'green',
                       'background': 'transparent',
                       'border': 'none',
                       'font-size': '34px'}
            ),
            dbc.Tooltip(
                "Compute features",
                id=FEATURES_COMPUTE_TOOLTIP,
                target=FEATURES_COMPUTE_BTN,
            )
        ],
            style={'text-align': 'center'}
        ),
        html.Div([
            dbc.Label("Compute features")
        ],
            style={'text-align': 'center'})
    ]),
    dbc.Row([
        html.P(),
        html.Hr(), html.Br(), html.Br(), html.Br(),
        html.H1('Computed features', style={'textAlign': 'center'})
    ]),
    dbc.Row([
        dbc.Col([
            select_computation_card
        ], width=2),
        dbc.Col([
            dcc.Loading(
                id=FEATURES_LOADING,
                type="default",
                children=dash_table.DataTable(
                    [{feature: ''
                      for feature in ComputedFeatures.features_list}],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        # all three widths are needed
                        'minWidth': '10%', 'width': '10%', 'maxWidth': '10%',
                        'textAlign': 'center'
                    },
                    style_header={'textAlign': 'center'},
                    id=FEATURES_TABLE
                )
            )
        ],
            style={'textAlign': 'center',
                   'margin-left': '0px'})
    ]),
    dbc.Row([
        html.Div([
            html.Button(
                className="fas fa-download",
                id=FEATURES_DOWNLOAD_BTN,
                style={'color': 'blue',
                       'background': 'transparent',
                       'border': 'none',
                       'font-size': '34px'}
            ),
            dbc.Tooltip(
                "Download features",
                id=FEATURES_DOWNLOAD_TOOLTIP,
                target=FEATURES_DOWNLOAD_BTN,
            ),
        ],
            style={'text-align': 'center'}),
        html.Div([
            dbc.Label("Download features")
        ],
            style={'text-align': 'center'})
    ]),
    dcc.Download(id=FEATURES_DOWNLOAD_DCC),
])
