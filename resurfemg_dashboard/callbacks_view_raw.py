"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

from dash import Input, Output, callback, ctx, State, ALL, callback_context
from resurfemg_dashboard.app import app, variables
from resurfemg_dashboard import utils
import numpy as np


@callback(Output('emg-graphs-container', 'children'),
          Output('emg-header', 'hidden'),
          Output('emg-filename', 'children'),
          Input('emg-delete-button', 'n_clicks'))
def show_raw_data(delete):
    emg_ts = variables.get_emg_timeseries()
    hidden = True

    trigger_id = ctx.triggered_id
    filename = variables.get_emg_filename()

    if trigger_id == 'emg-delete-button':
        variables.set_emg_filename(None)
        variables.set_emg_timeseries(None)
        children_emg = []
    else:
        if emg_ts is not None:
            emg_fs = variables.get_fs_emg()
            plot_data, plot_info = utils.update_plot_data(
                new_data=emg_ts.to_numpy(signal_io=('raw',)),
                new_info={'signal': 'Raw', 'color': 'blue', 'secondary': False,
                          'visible': True}
            )
            titles = emg_ts.labels
            units = emg_ts.y_units
            children_emg = utils.add_emg_graphs(
                plot_data, plot_info, emg_fs, titles=titles, units=units)
            hidden = False
        else:
            children_emg = []

    return children_emg, hidden, filename


@callback(Output('ventilator-graphs-container', 'children'),
          Output('ventilator-header', 'hidden'),
          Output('ventilator-filename', 'children'),
          Input('ventilator-delete-button', 'n_clicks'))
def show_raw_data(delete):
    vent_ts = variables.get_vent_timeseries()
    hidden = True

    trigger_id = ctx.triggered_id
    filename = variables.get_ventilator_filename()

    if trigger_id == 'ventilator-delete-button':
        variables.set_ventilator_filename(None)
        variables.set_vent_timeseries(None)
        children_vent = []
    else:
        if vent_ts is not None:
            fs_vent = variables.get_fs_vent()
            plot_data, plot_info = utils.update_plot_data(
                new_data=vent_ts.to_numpy(signal_io=('raw',)),
                new_info={'signal': 'Raw', 'color': 'blue', 'secondary': False,
                          'visible': True}
            )
            titles = vent_ts.labels
            units = vent_ts.y_units

            children_vent = utils.add_ventilator_graphs(
                plot_data, plot_info, fs_vent, titles=titles, units=units)
            hidden = False
        else:
            children_vent = []

    return children_vent, hidden, filename


@app.callback(
    Output({"type": "dynamic-graph", "index": ALL}, "figure"),
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
    fig_list = []
    for idx, key in enumerate(graph_id_list):
        relayoutdata = relayoutdata_list[idx]
        fig = utils.get_graph_fig(dict_key=key)
        if relayoutdata and relayoutdata_src:
            if 'xaxis.range[0]' in relayoutdata_src:
                x_range_new = [relayoutdata_src['xaxis.range[0]'],
                               relayoutdata_src['xaxis.range[1]']]
                relayoutdata.pop('xaxis.autorange', None)
                relayoutdata['xaxis.range[0]'] = x_range_new[0]
                relayoutdata['xaxis.range[1]'] = x_range_new[1]
            elif 'xaxis.autorange' in relayoutdata_src:
                relayoutdata['xaxis.autorange'] = True
                relayoutdata.pop('xaxis.range[0]', None)
                relayoutdata.pop('xaxis.range[1]', None)
            if 'dragmode' in relayoutdata_src:
                relayoutdata['dragmode'] = relayoutdata_src['dragmode']
                fig.update_layout(dragmode=relayoutdata_src['dragmode'])
        fig_list.append(fig.construct_update_data_patch(relayoutdata))

    return fig_list
