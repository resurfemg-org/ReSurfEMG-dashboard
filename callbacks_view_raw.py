"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

from dash import Input, Output, callback, ctx, MATCH, State
from app import app, variables
import utils
import numpy as np


@callback(Output('emg-graphs-container', 'children'),
          Output('emg-header', 'hidden'),
          Output('emg-filename', 'children'),
          Input('emg-delete-button', 'n_clicks'))
def show_raw_data(delete):
    emg_data = variables.get_emg()
    hidden = True

    trigger_id = ctx.triggered_id
    filename = variables.get_emg_filename()

    if trigger_id == 'emg-delete-button':
        variables.set_emg(None)
        variables.set_emg_filename(None)
        variables.set_emg_timeseries(None)
        children_emg = []
    else:
        if emg_data is not None:
            emg_frequency = variables.get_emg_freq()
            children_emg = utils.add_emg_graphs(np.array(emg_data), emg_frequency)
            hidden = False
        else:
            children_emg = []

    return children_emg, hidden, filename


@callback(Output('ventilator-graphs-container', 'children'),
          Output('ventilator-header', 'hidden'),
          Output('ventilator-filename', 'children'),
          Input('ventilator-delete-button', 'n_clicks'))
def show_raw_data(delete):
    ventilator_data = variables.get_ventilator()
    hidden = True

    trigger_id = ctx.triggered_id
    filename = variables.get_ventilator_filename()

    if trigger_id == 'ventilator-delete-button':
        variables.set_ventilator(None)
        variables.set_ventilator_filename(None)
        variables.set_vent_timeseries(None)
        children_vent = []
    else:
        if ventilator_data is not None:
            ventilator_frequency = variables.get_ventilator_freq()
            children_vent = utils.add_ventilator_graphs(np.array(ventilator_data), ventilator_frequency)
            hidden = False
        else:
            children_vent = []

    return children_vent, hidden, filename


@app.callback(
    Output({"type": "dynamic-updater", "index": MATCH}, "updateData"),
    Input({"type": "dynamic-graph", "index": MATCH}, "relayoutData"),
    State({"type": "dynamic-graph", "index": MATCH}, "id"),
    prevent_initial_call=True,
)
def update_figure(relayoutdata: dict, graph_id_dict: dict):
    return utils.get_dict(graph_id_dict, relayoutdata)
