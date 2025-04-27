"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

import utils
from app import variables
from dash import Input, Output, callback
import plotly.graph_objects as go
from plotly_resampler import FigureResampler


@callback(Output({"type": "dynamic-graph", "index": "emgventilator"}, 'figure'),
          Input('emgventilator-secret-div', 'data'))
def update_figure(data):
    emg_data = variables.get_emg_processed()
    emg_fs = variables.get_emg_freq()
    ventilator_data = variables.get_ventilator()
    ventilator_fs = variables.get_ventilator_freq()

    if emg_data.ndim == 1:
        time_array_emg = utils.get_time_array(emg_data.shape[0], emg_fs)
    else:
        time_array_emg = utils.get_time_array(emg_data.shape[1], emg_fs)

    time_array_ventilator = utils.get_time_array(ventilator_data.shape[1], ventilator_fs)

    fig = FigureResampler(go.Figure())
    fig.add_trace(go.Scatter(),
                  hf_x=time_array_emg,
                  hf_y=emg_data)
    fig.add_trace(go.Scatter(),
                  hf_x=time_array_ventilator,
                  hf_y=ventilator_data[1, :],
                  secondary_ys=[False,True])

    fig.update_layout(
        xaxis_title="Time [s]",
        yaxis_title="micro Volts",
        legend_title="Legend Title"
    )

    utils.set_dict("emgventilator",fig)

    return fig
