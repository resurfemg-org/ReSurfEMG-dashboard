"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

from typing import Any, Tuple

import numpy as np
import os
from dash import (Input, Output, callback, ctx, State, html, ALL,
                  callback_context, no_update)
                  
from app import app, variables
from resurfemg.data_connector import config
from resurfemg.data_connector import converter_functions as cv
from resurfemg.data_connector.data_classes import (
    EmgDataGroup, VentilatorDataGroup)
from pathlib import Path
from dash.exceptions import PreventUpdate
from definitions import (
    PATH_BTN, FILE_PATH_INPUT, PATH_SELECT, CWD, CWD_FILES, CONFIRM_CENTERED,
    MODAL_CENTERED, EMG_OPEN_CENTERED, VENT_OPEN_CENTERED, PARENT_DIR,
    LISTED_FILES, VENT_fs_DIV, VENT_SAMPLING_fs,
    EMG_fs_DIV, EMG_SAMPLING_fs, VENT_FILE_UPDATED,
    EMG_FILE_UPDATED, PATH_ERROR, DIR_FAVORITES, EMG_SAMPLING_fs,
    INVALID_DIR)

# variable to keep track of which upload button has been clicked
clicked_input_btn = None

def convert_to_os_path(
    path: str,
):
    """
    This function converts a path to a os readable path.
    -----------------------------------------------------------------------
    :param path: The path to convert.
    :type path: str
    """
    readable_path = path.replace(
        os.sep if os.altsep is None else os.altsep, os.sep)
    return readable_path

@callback(Output(EMG_fs_DIV, 'data'),
          Input(EMG_SAMPLING_fs, 'value'))
def update_emg_fs(freq, ):
    variables.set_emg_freq(freq)
    return 'set'


@callback(Output(VENT_fs_DIV, 'data'),
          Input(VENT_SAMPLING_fs, 'value'))
def update_ventilator_fs(freq):
    variables.set_ventilator_freq(freq)
    return 'set'


@app.callback(
    [Output(MODAL_CENTERED, 'is_open'), Output(EMG_FILE_UPDATED, 'children'), Output(VENT_FILE_UPDATED, 'children')],
    [Input(EMG_OPEN_CENTERED, 'n_clicks'), Input(VENT_OPEN_CENTERED, 'n_clicks'), Input(CONFIRM_CENTERED, 'n_clicks')],
    [State(MODAL_CENTERED, 'is_open'), State(PATH_SELECT, 'data'),
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
    Output(CWD, 'value'),
    Output(PATH_ERROR, 'children'),
    Output(CWD_FILES, 'children'),
    Output(DIR_FAVORITES, 'children'),
    Input(PATH_SELECT, 'data'),
    Input(PARENT_DIR, 'n_clicks'),
    State(CWD, 'value'),
    Input(PATH_BTN, 'n_clicks'),

)
def get_parent_directory_emg(selected_path, n_clicks, cwd, path_btn):
    triggered_id = callback_context.triggered_id
    path = None
    dir_inputs = [
        ('Home', os.getcwd(), '🏠'), 
        ('User', os.path.expanduser('~'), '👤'),
        ('Computer', os.path.abspath(os.sep), '💻'),
    ]
    _config = config.Config(verbose=False)
    config_paths = _config.get_config()
    if config_paths:
        for _dir_name, _dir_path in config_paths.items():
            dir_inputs.append((_dir_name, _dir_path, '⭐'))

    dir_list = []
    false_dirs = 0
    for i, (_dir_name, _dir_path, icon) in enumerate(dir_inputs):
        style={
            'color': 'black',
            'whiteSpace': 'nowrap',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'display': 'inline-flex',
            'alignItems': 'center',
            'maxWidth': '125px'}

        if os.path.exists(_dir_path):
            link = html.A([html.Span(
                _dir_name,
                id={'type': DIR_FAVORITES,'index': i-false_dirs},
                title=convert_to_os_path(_dir_path),
                style=style,
            )], href='#')
        else:
            false_dirs += 1
            style['color'] = 'red'
            link = html.A([html.Span(
                _dir_name, id={'type': INVALID_DIR, 'index': i},
                title=convert_to_os_path(_dir_path),
                style=style
            )], href='#')
            icon = '❌'

        if icon:
            dir_list.append(icon)
        else:
            dir_list.append('📂')
        dir_list.append(link)
        dir_list.append(html.Br())

    if triggered_id == PATH_SELECT:
        path = selected_path
    elif triggered_id == PATH_BTN:
        path = convert_to_os_path(Path(cwd).as_posix())
    elif triggered_id == PARENT_DIR:
        path = convert_to_os_path(Path(cwd).parent.as_posix())

    if path is None:
        path = os.getcwd()

    if os.path.exists(path) or os.path.isfile(path):
        path_error = ''
    else:
        path_error = 'Path not valid'
    
    cwd_files = []
    if path and Path(path).is_dir():
        work_path = Path(path)
        sel_path = None
    elif path and Path(path).is_file():
        work_path = Path(path).parent
        sel_path = path
    else:
        work_path = None
        sel_path = None

    if work_path:
        files = sorted(os.listdir(work_path), key=str.lower)
        for i, file in enumerate(files):
            filepath = Path(file)
            full_path = os.path.join(work_path, filepath.as_posix())

            is_dir = Path(full_path).is_dir()
            is_sel_file = sel_path == convert_to_os_path(full_path)
            style = {
                'color': 'black',
                'whiteSpace': 'nowrap',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'display': 'inline-flex',
                'alignItems': 'center',
                'maxWidth': '500px',
            }
            # style = {}
            if is_dir:
                style['fontWeight'] = 'bold'
            elif is_sel_file:
                style['backgroundColor'] = 'yellow'
            
            link = html.A([
                html.Span(
                    file, id={'type': LISTED_FILES, 'index': i},
                    title=full_path,
                    style=style,
                )], href='#')
            prepend = '🗒️' if not is_dir else '📂'
            cwd_files.append(prepend)
            cwd_files.append(link)
            cwd_files.append(html.Br())

    return path, path_error, cwd_files, dir_list


@app.callback(
    Output(PATH_SELECT, 'data'),
    Input({'type': LISTED_FILES, 'index': ALL}, 'n_clicks'),
    State({'type': LISTED_FILES, 'index': ALL}, 'children'),
    State({'type': LISTED_FILES, 'index': ALL}, 'title'),
    Input({'type': DIR_FAVORITES, 'index': ALL}, 'n_clicks'),
    State({'type': DIR_FAVORITES, 'index': ALL}, 'children'),
    State({'type': DIR_FAVORITES, 'index': ALL}, 'title'),
    State(CWD, 'children'))
def store_clicked_file(
    n_clicks_f, href_f, title_f, n_clicks_d, href_d, title_d, cwd):
    if ((not n_clicks_f or set(n_clicks_f) == {None})
        and (not n_clicks_d or set(n_clicks_d) == {None})):
        raise PreventUpdate
    trigger = ctx.triggered_id
    index = ctx.triggered_id['index']
    if trigger['type'] == LISTED_FILES:
        title = title_f[index] 
    else:
        title = title_d[index]
    return title


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
