"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

import dash
import dash_bootstrap_components as dbc
import definitions
from dash import html, dcc

import utils
from definitions import EnvelopeMethod

dash.register_page(__name__, path='/preprocessing')

tailcut_card = dbc.Card([
    dbc.CardHeader("Cut tail"),
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.P("Tail portion [%]"),
                dcc.Input(
                    id='tail-cut-percent',
                    type="number",
                    placeholder="%",
                    value=definitions.default_first_cut_percentage
                )
            ]),
            dbc.Col([
                html.P("Tolerance on variation"),
                dcc.Input(
                    id='tail-cut-tolerance',
                    type="number",
                    placeholder="%",
                    value=definitions.default_first_cut_tolerance
                )
            ])
        ])
    ])
])

baseline_card = dbc.Card([
    dbc.CardHeader("Baseline removal"),
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.P("Low cut frequency"),
                dcc.Input(
                    id='base-filter-low',
                    type="number",
                    placeholder="low cut",
                    value=definitions.default_bandpass_low
                )
            ]),
            dbc.Col([
                html.P("High cut frequency"),
                dcc.Input(
                    id='base-filter-high',
                    type="number",
                    placeholder="high cut",
                    value=definitions.default_bandpass_high
                )
            ])
        ])
    ])
])

ecg_card = dbc.Card([
    dbc.CardHeader("ECG removal"),
    utils.get_ecg_removal_layout({"type": "ecg-filter-select", "index": "0"})
],
    id={"type": "ecg-removal-type", "index": "0"})

envelope_card = dbc.Card([
    dbc.CardHeader("Envelope extraction"),
    dbc.Label("Envelope computation method"),
    dbc.Select(
        id="envelope-extraction-select",
        options=[
            {"label": "RMS", "value": EnvelopeMethod.RMS},
            {"label": "Filtering", "value": EnvelopeMethod.FILTERING},
            {"label": "None", "value": EnvelopeMethod.NONE},
        ],
        value=definitions.default_envelope_value
    )
])

layout = html.Div([
    html.P(),
    html.Div(id='emg-filename-preprocessing'),
    dbc.Row([
        html.Span([
            html.Button(
                className="fas fa-download",
                id='download-data-btn',
                style={'color': 'blue',
                       'background': 'transparent',
                       'border': 'none',
                       'font-size': '34px'},
                disabled=True,
            ),
            dbc.Tooltip(
                "Save data",
                id="tooltip-download-data",
                target="download-data-btn",
            )
        ]),
        dcc.Download(id="download-params"),
        dcc.Download(id="download-emg-processed")
    ],
        style={'text-align': 'center'}
    ),
    html.P(),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    dbc.Switch(
                        id="pipeline-switch",
                        label="Custom pipeline",
                        value=False
                    ),
                ], "Processing pipeline", style={'text-align': 'center'}
                ),
                dbc.Collapse([
                    html.P(),
                    dbc.Col([
                        dbc.Row([
                            dbc.Alert(
                                "The file is not valid",
                                id="alert-invalid-file",
                                dismissable=True,
                                is_open=False,
                                duration=4000,
                                color="danger",
                                style={'width': 'auto',
                                       'left': '18px'}
                            ),
                            dcc.Upload(
                                className="fas fa-upload",
                                id='upload-processing-params',
                                accept='application/json',
                                style={'color': 'blue',
                                       'background': 'transparent',
                                       'border': 'none',
                                       'font-size': '34px'},
                            ),
                            dbc.Tooltip(
                                "Upload the parameters file",
                                id="tooltip-upload-params",
                                target="upload-processing-params",
                            )
                        ],
                            style={'text-align': 'center'}),
                        html.Div("Upload the parameters file",
                                 style={'text-align': 'center'}),
                        html.P(),
                        dbc.Row([
                            html.Button(
                                className="fas fa-undo",
                                id='restore-default-btn',
                                style={'color': 'black',
                                       'background': 'transparent',
                                       'border': 'none',
                                       'font-size': '34px'},
                            ),
                            dbc.Tooltip(
                                "Restore default pipeline",
                                id="tooltip-restore-pipeline",
                                target="restore-default-btn",
                            )
                        ],
                            style={'text-align': 'center'}),
                        html.Div("Restore default pipeline",
                                 style={'text-align': 'center'}),

                        tailcut_card,
                        html.P(),
                        baseline_card,
                        html.P(),
                        ecg_card,
                        html.P(),
                        html.Div([], id='custom-preprocessing-steps'),

                        html.Div([
                            html.Button(
                                className="fas fa-plus-circle",
                                id='add-steps-btn',
                                style={'color': 'blue',
                                       'background': 'transparent',
                                       'border': 'none',
                                       'font-size': '34px'}),
                            dbc.Tooltip(
                                "Add new step",
                                id="tooltip-add-step",
                                target="add-steps-btn",
                            )
                        ],
                            style={'text-align': 'center'}
                        ),
                        html.P(),
                        envelope_card
                    ]),
                    html.P(),
                    html.Div([
                        html.Button(
                            className="fas fa-play",
                            id='apply-pipeline-btn',
                            style={'color': 'green',
                                   'background': 'transparent',
                                   'border': 'none',
                                   'font-size': '34px'}
                        ),
                        dbc.Tooltip(
                            "Apply processing",
                            id="tooltip-apply-pipeline",
                            target="apply-pipeline-btn",
                        )
                    ],
                        style={'text-align': 'center'}
                    ),
                    html.P(),

                ],
                    id='pipeline-card-body',
                    is_open=False),
            ])
        ], width=2),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Processed signals", style={'text-align': 'center'}),
                html.Div(id='preprocessing-processed-container'),
            ]),

        ], width=10, id='processed-signals-column'),
        # dbc.Col([
        #     dbc.Card([
        #         dbc.CardHeader([
        #             html.Button(
        #                 className="fas fa-angle-left",
        #                 id='open-column-btn',
        #                 style={'color': 'blue',
        #                        'background': 'transparent',
        #                        'border': 'none',
        #                        'font-size': '24px'},
        #             ),
        #             dbc.Label("Raw Signal"),
        #         ], style={'text-align': 'left'}
        #         ),
        #         dbc.Collapse([
        #             html.Div(id='preprocessing-original-container'),
        #         ], is_open=False, id='collapse-raw')
        #     ]),
        # ], width=1, id='raw-signals-column'),
        html.Div(id='load-preprocessing-div')
    ]),
    html.P(),
    dcc.ConfirmDialog(
        id='confirm-upload',
        message='Uploading the parameters will overwrite the current settings. Are you sure you want to continue?',
    ),
    dcc.ConfirmDialog(
        id='confirm-reset',
        message='Resetting the parameters will overwrite the current settings. Are you sure you want to continue?',
    ),
])
