"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

from dash import Input, Output, callback, ctx, MATCH, State, ALL, callback_context
from app import app, variables
import utils
import numpy as np
from dash.exceptions import PreventUpdate


@callback(Output('emg-graphs-container', 'children'),
          Output('emg-header', 'hidden'),
          Output('emg-filename', 'children'),
          Input('emg-delete-button', 'n_clicks'))
def show_raw_data(delete):
    emg_data = variables.get_emg()
    emg_timeseries = variables.get_emg_timeseries()
    if emg_timeseries is not None:
        titles = [ts.label for ts in emg_timeseries]
        units = [ts.y_units for ts in emg_timeseries]
    else:
        titles = None
        units = None
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
            children_emg = utils.add_emg_graphs(
                np.array(emg_data), emg_frequency, titles=titles, units=units)
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
    Output({"type": "dynamic-updater", "index": ALL}, "updateData"),
    Input({"type": "dynamic-graph", "index": ALL}, "relayoutData"),
    State({"type": "dynamic-graph", "index": ALL}, "id"),
    prevent_initial_call=True,
)
def update_figure(relayoutdata_list: dict, graph_id_dict_list: dict):
    triggered_index = callback_context.triggered[0]["prop_id"].split(
        '{"index":"')[1].split('","type')[0]
    graph_id_list = [d["index"] for d in graph_id_dict_list]
    src_idx = graph_id_list.index(triggered_index)
    relayoutdata_src = relayoutdata_list[src_idx]
    if relayoutdata_src is not None and 'xaxis.range[0]' in relayoutdata_src:
        x_range_new = [relayoutdata_src['xaxis.range[0]'],
                       relayoutdata_src['xaxis.range[1]']]

    updateData_list = []
    for idx, key in enumerate(graph_id_list):
        relayoutdata = relayoutdata_list[idx]
        graph_id_dict = graph_id_dict_list[idx]
        if relayoutdata is not None:
            if (relayoutdata_src is not None
                    and 'xaxis.range[0]' in relayoutdata_src):
                relayoutdata.pop('xaxis.autorange', None)
                relayoutdata.pop('xaxis.showspikes', None)
                relayoutdata['xaxis.range[0]'] = x_range_new[0]
                relayoutdata['xaxis.range[1]'] = x_range_new[1]
                fig = utils.get_graph_fig(dict_key=key)
                fig.update_xaxes(range=x_range_new, overwrite=True)
                fig.update_xaxes(showgrid=False)
            else:
                relayoutdata['xaxis.autorange'] = True
                relayoutdata['xaxis.showspikes'] = True
                relayoutdata.pop('xaxis.range[0]', None)
                relayoutdata.pop('xaxis.range[1]', None)
                fig = utils.get_graph_fig(dict_key=key)
                fig.update_xaxes(autorange=True, overwrite=True)
        updateData = utils.get_dict(graph_id_dict, relayoutdata)
        updateData_list.append(updateData)

    return updateData_list
