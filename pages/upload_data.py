"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""
import os

import dash
import dash_bootstrap_components as dbc
from definitions import (PATH_BTN, FILE_PATH_INPUT, PATH_SELECT, CWD,
                         CWD_FILES, CONFIRM_CENTERED, MODAL_CENTERED,
                         EMG_OPEN_CENTERED, VENT_OPEN_CENTERED, PARENT_DIR,
                         EMG_SAMPLING_FREQUENCY, VENT_SAMPLING_FREQUENCY,
                         VENT_FREQUENCY_DIV, EMG_FREQUENCY_DIV,
                         VENT_FILE_UPDATED, EMG_FILE_UPDATED, PATH_ERROR,
                         DIR_FAVORITES)
from dash import html, dcc

dash.register_page(__name__, path='/')

modal_dialog = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Select file"), close_button=True),
                dbc.ModalBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button('↑', id=PARENT_DIR)
                        ], width=1, className="d-grid gap-2"),
                        dbc.Col([
                            dcc.Input(
                                id=CWD,
                                value=os.getcwd(),
                                placeholder='Insert the path to the file')
                        ], className="d-grid gap-2"),
                        dbc.Col([
                            dbc.Button('↵', id=PATH_BTN)
                        ], width=1, className="d-grid gap-2"),
                    ], class_name="py-2"),
                    dbc.Row([
                        html.P(id=PATH_ERROR, style={'color': 'red'}),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Div(
                                id=DIR_FAVORITES,
                                style={
                                    'overflowY': 'scroll', 'height': '400px'})
                        ], width=3, className="d-grid gap-2"),
                        dbc.Col([
                            html.Div(
                                id=CWD_FILES,
                                style={
                                    'overflowY': 'scroll', 'height': '400px'})
                        ], width=9, className="d-grid gap-2"),
                        dcc.Store(id=PATH_SELECT, data=os.getcwd()),
                        # html.H3([html.Code(os.getcwd(), id=CWD)]),
                    ])]),
                dbc.ModalFooter(
                    dbc.Button(
                        "Confirm",
                        id=CONFIRM_CENTERED,
                        className="ms-auto",
                        n_clicks=0,
                    )
                ),
            ],
            id=MODAL_CENTERED,
            centered=True,
            is_open=False,
            backdrop=False,
            scrollable=True,
            size='lg',
        ),
    ]
)


def layout():
    return html.Div([

        html.H1('Upload Data'),
        modal_dialog,
        dbc.Row([
            dbc.Col([html.Div([
                dbc.Button("UPLOAD EMG DATA", id=EMG_OPEN_CENTERED),
            ],
                className="d-grid gap-2"),

            ], width=6),

            dbc.Col([html.Div([
                dcc.Input(
                    id=EMG_SAMPLING_FREQUENCY,
                    type="number",
                    placeholder="EMG sampling frequency",
                    value=2048
                ),
            ],
                style={'textAlign': 'right'}),
            ], width=2),

            dbc.Col([
                html.Div('EMG sampling frequency', style={'textAlign': 'left'})
            ], width=2),
            html.P(),
            html.Div(id=EMG_FILE_UPDATED),
        ]),

        dbc.Row([html.P()]),
        dbc.Row([
            dbc.Col([html.Div([
                dbc.Button("UPLOAD VENTILATOR DATA", id=VENT_OPEN_CENTERED),
            ],
                className="d-grid gap-2"),

            ], width=6),

            dbc.Col([html.Div([

                dcc.Input(
                    id=VENT_SAMPLING_FREQUENCY,
                    type="number",
                    placeholder="Ventilator sampling frequency",
                    value=100
                ),
            ],
                style={'textAlign': 'right'}),
            ], width=2),

            dbc.Col([
                html.Div('Ventilator sampling frequency', style={'textAlign': 'left'})
            ], width=2),
            html.P(),
            html.Div(id=VENT_FILE_UPDATED),
        ]),
        # the following elements are only needed
        # to provide outputs to the callbacks
        html.Div(id=EMG_FREQUENCY_DIV),
        html.Div(id=VENT_FREQUENCY_DIV)
    ])
