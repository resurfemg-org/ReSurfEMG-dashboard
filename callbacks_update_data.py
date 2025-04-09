"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

from typing import Any, Tuple

import numpy as np
import os
from dash import Input, Output, callback, ctx, State, html, ALL, callback_context
from app import app, variables
from resurfemg.data_connector import converter_functions as cv
from resurfemg.data_connector.data_classes import (
    EmgDataGroup, VentilatorDataGroup)
from pathlib import Path
from dash.exceptions import PreventUpdate
from definitions import (
    PATH_BTN, FILE_PATH_INPUT, STORED_CWD, CWD, CWD_FILES, CONFIRM_CENTERED,
    MODAL_CENTERED, EMG_OPEN_CENTERED, VENT_OPEN_CENTERED, PARENT_DIR,
    LISTED_FILES, VENT_FREQUENCY_DIV, VENT_SAMPLING_FREQUENCY,
    EMG_FREQUENCY_DIV, EMG_SAMPLING_FREQUENCY, VENT_FILE_UPDATED,
    EMG_FILE_UPDATED)

# variable to keep track of which upload button has been clicked
clicked_input_btn = None


@callback(Output(EMG_FREQUENCY_DIV, 'data'),
          Input(EMG_SAMPLING_FREQUENCY, 'value'))
def update_emg_frequency(freq, ):
    variables.set_emg_freq(freq)
    return 'set'


@callback(Output(VENT_FREQUENCY_DIV, 'data'),
          Input(VENT_SAMPLING_FREQUENCY, 'value'))
def update_ventilator_frequency(freq):
    variables.set_ventilator_freq(freq)
    return 'set'


@app.callback(
    [Output(MODAL_CENTERED, 'is_open'), Output(EMG_FILE_UPDATED, 'children'), Output(VENT_FILE_UPDATED, 'children')],
    [Input(EMG_OPEN_CENTERED, 'n_clicks'), Input(VENT_OPEN_CENTERED, 'n_clicks'), Input(CONFIRM_CENTERED, 'n_clicks')],
    [State(MODAL_CENTERED, 'is_open'), State(STORED_CWD, 'data'),
     State(EMG_FILE_UPDATED, 'children'), State(VENT_FILE_UPDATED, 'children')],
    prevent_initial_call=True
)
def toggle_modal(n1, n2, n3, is_open, selected_file, current_msg_emg, current_msg_vent):
    global clicked_input_btn

    message_emg = current_msg_emg
    message_vent = current_msg_vent

    if ctx.triggered_id in [EMG_OPEN_CENTERED, VENT_OPEN_CENTERED]:
        clicked_input_btn = ctx.triggered_id

    if ctx.triggered_id == CONFIRM_CENTERED:
        data, metadata = read_file(selected_file)
        
        if data is not None:
            if clicked_input_btn == EMG_OPEN_CENTERED:
                variables.set_emg(data)
                variables.set_emg_filename('File: ' + selected_file)
                emg_timeseries = EmgDataGroup(
                    y_raw=data,
                    fs=metadata['fs'] if 'fs' in metadata else None,
                    labels=metadata['labels'] if 'labels' in metadata else None,
                    units=metadata['units'] if 'units' in metadata else None,
                )
                variables.set_emg_timeseries(emg_timeseries)
                message_emg = 'File correctly uploaded: ' + selected_file
            elif clicked_input_btn == VENT_OPEN_CENTERED:
                variables.set_ventilator(data)
                variables.set_ventilator_filename('File: ' + selected_file)
                vent_timeseries = VentilatorDataGroup(
                    y_raw=data,
                    fs=metadata['fs'] if 'fs' in metadata else None,
                    labels=metadata['labels'] if 'labels' in metadata else None,
                    units=metadata['units'] if 'units' in metadata else None,
                )
                variables.set_vent_timeseries(vent_timeseries)
                message_vent = 'File correctly uploaded: ' + selected_file
        else:
            if clicked_input_btn == EMG_OPEN_CENTERED:
                message_emg = 'The selected file is not valid'
            elif clicked_input_btn == VENT_OPEN_CENTERED:
                message_vent = 'The selected file is not valid'

    return not is_open, message_emg, message_vent


@app.callback(
    Output(CWD, 'children'),
    State(FILE_PATH_INPUT, 'value'),
    Input(STORED_CWD, 'data'),
    Input(PARENT_DIR, 'n_clicks'),
    Input(CWD, 'children'),
    Input(PATH_BTN, 'n_clicks'),
    prevent_initial_call=True)
def get_parent_directory_emg(path_input, stored_cwd, n_clicks, currentdir, path_btn):
    triggered_id = callback_context.triggered_id
    path = None

    if triggered_id == STORED_CWD:
        path = stored_cwd
    elif triggered_id == PATH_BTN:
        path = Path(path_input).parent.as_posix()
    elif triggered_id == PARENT_DIR:
        path = Path(currentdir).parent.as_posix()

    return path if os.path.exists(path) or os.path.isfile(path) else 'Path not valid'


@app.callback(
    Output(CWD_FILES, 'children'),
    Input(CWD, 'children'))
def list_cwd_files(cwd):
    path = Path(cwd)

    cwd_files = []
    if path.is_dir():
        files = sorted(os.listdir(path), key=str.lower)
        for i, file in enumerate(files):
            filepath = Path(file)
            full_path = os.path.join(cwd, filepath.as_posix())

            is_dir = Path(full_path).is_dir()
            link = html.A([
                html.Span(
                    file, id={'type': LISTED_FILES, 'index': i},
                    title=full_path,
                    style={'fontWeight': 'bold'} if is_dir else {}
                )], href='#')
            prepend = '' if not is_dir else '📂'
            cwd_files.append(prepend)
            cwd_files.append(link)
            cwd_files.append(html.Br())

    return cwd_files


@app.callback(
    Output(STORED_CWD, 'data'),
    Input({'type': LISTED_FILES, 'index': ALL}, 'n_clicks'),
    State({'type': LISTED_FILES, 'index': ALL}, 'children'),
    State({'type': LISTED_FILES, 'index': ALL}, 'title'),
    State(CWD, 'children'))
def store_clicked_file(n_clicks, href, title, cwd):
    if not n_clicks or set(n_clicks) == {None}:
        raise PreventUpdate
    index = ctx.triggered_id['index']
    return title[index]


def read_file(file_path: str) -> np.ndarray:
    """
    Read the file specified in file_path and returns the file content.
        Args:
            file_path: the local path of the file
        Returns:
            A ndarray containing the leads, or None if the file is not valid
    """
    try:
        try:
            data, _, metadata = cv.load_file(file_path, verbose=False)
        except Exception as e:
            raise Exception(f"Error loading file: {e}")
    except:
        data = None
        metadata = None

    return data, metadata
