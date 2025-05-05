"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

from copy import deepcopy
import dash
import definitions
import json
import numpy as np
import pandas as pd
import utils
from utils import colors
from app import variables
from dash import Input, Output, State, callback, MATCH, ALL, html, ctx, dcc
from definitions import FILE_IDENTIFIER
from resurfemg.data_connector.data_classes import EmgDataGroup

card_counter = 0
json_parameters = []


# on loading add the emg graphs
@callback(Output('emg-filename-preprocessing', 'children'),
          Input('load-preprocessing-div', 'data'))
def show_raw_data(data):
    global card_counter

    filename = variables.get_emg_filename()

    return filename


# apply the processing on the button click
@callback(Output('preprocessing-processed-container', 'children'),
          Output('download-data-btn', 'disabled'),
          Input('apply-pipeline-btn', 'n_clicks'),
          State({"type": "additional-step-core", "index": ALL}, "id"),
          State({"type": "additional-step-type", "index": ALL}, "value"),
          State({"type": "additional-step-core", "index": ALL}, "children"))
def show_data(click, cards, steps, steps_args):
    # variables initialization
    global json_parameters

    # Reset the list of processing steps parameters
    json_parameters.clear()
    # Added to easily verify the file compatibility when uploaded
    json_parameters.append({'file_identifier': FILE_IDENTIFIER})

    # emg_data = variables.get_emg()
    emg_ts = variables.get_emg_timeseries()
    fs = variables.get_fs_emg()

    trigger = ctx.triggered_id
    # Set the default processing pipeline
    default_settings = definitions.get_default_pipeline(fs_emg=2048)
    def_opts = {}
    for i, (method, options) in enumerate(default_settings.items()):
        def_opts[i] = {}
        def_opts[i]['method'] = method
        def_opts[i]['args_val'] = {}
        for arg_name, arg_value in options['arg_defaults'].items():
            def_opts[i]['args_val'][arg_name] = arg_value
        set_args = options['set_args']
        for arg_name in set_args:
            def_opts[i]['args_val'][arg_name] = set_args[arg_name]


    # if data have been loaded, apply the processing
    if emg_ts is not None:
        if trigger is not None:
            # Process the selected processing pipeline
            sel_opts = utils.parse_preprocessing_options(
                cards, steps, steps_args, fs_emg=fs)
            custom_pipeline = def_opts != sel_opts
        else:
            custom_pipeline = False
        if def_opts != variables.get_default_pipeline() or not all(
            key in emg_ts[0] for key in ('clean_default', 'env_default')):
            variables.set_default_pipeline(deepcopy(def_opts))
            emg_ts = utils.apply_processing_pipeline(
                emg_ts, pipeline=def_opts, suffix='_default')
        titles = emg_ts.labels
        units = emg_ts.y_units

        signals = [
            ('raw', 'Raw', 'black', True, 'legendonly'),
            ('clean_default', 'Filtered (Default)', colors['blue1'], False,
              'legendonly' if custom_pipeline else True),
            ('env_default', 'Envelope (Default)', 'red', False, True)
        ]
        if custom_pipeline:
            if sel_opts != variables.get_custom_pipeline() or not all(
                key in emg_ts[0] for key in ('clean_custom', 'env_custom')):
                variables.set_custom_pipeline(deepcopy(sel_opts))
                emg_ts = utils.apply_processing_pipeline(
                    emg_ts, pipeline=sel_opts, suffix='_custom')
            signals.append(
                ('clean_custom', 'Filtered', 'blue', False, True))
            signals.append(
                ('env_custom', 'Envelope', 'orange', False, True))
        plot_data = None
        plot_info = None
        for signal_io, signal_name, color, secondary, visibility in signals:
            plot_data, plot_info = utils.update_plot_data(
                new_data=emg_ts.to_numpy(signal_io=(signal_io,)),
                new_info={'signal': signal_name, 'color': color,
                        'secondary': secondary, 'visible': visibility},
                prev_data=plot_data, prev_info=plot_info
            )

        children_emg = utils.add_emg_graphs(
            plot_data, plot_info, fs, titles, units)
        # enable the data download
        save_data_enabled = False
    else:  # if no data have been uploaded
        children_emg = []
        save_data_enabled = True

    return children_emg, save_data_enabled


# open/close pipeline card
@callback(Output('pipeline-card-body', 'is_open'),
          Input('pipeline-switch', 'value'))
def show_raw_data(toggle_value):
    return toggle_value


# open/close EMG graphs
@callback(
    Output({"type": "emg-graph-collapse", "index": MATCH}, "is_open"),
    Input({"type": "emg-graph-switch", "index": MATCH}, "value"),
    prevent_initial_call=True
)
def collapse_graph(toggle_value):
    return toggle_value


# add/remove custom steps
@callback(Output('custom-preprocessing-steps', 'children'),
          Input('add-steps-btn', 'n_clicks'),
          Input({"type": "step-close-button", "index": ALL}, "n_clicks"),
          Input('confirm-upload', 'submit_n_clicks'),
          Input('confirm-reset', 'submit_n_clicks'),
          State('upload-processing-params', 'contents'),
          State('custom-preprocessing-steps', 'children'),
          prevent_initial_call=False)
def add_step(click, close, confirm_upload, confirm_reset, params_file,
             previous_content):
    global card_counter

    id_ctx = ctx.triggered_id
    # if the page is reloaded the steps are reset
    if id_ctx is None:
        card_counter = 0
        default_cards = []
        for i, method in enumerate(definitions.get_default_pipeline()):
            default_cards.append(
                utils.get_new_step_body(i, default=True, method=method))
            default_cards.append(html.P())
            card_counter += 1
        return default_cards
    # if the add steps button is clicked add the card
    elif id_ctx == 'add-steps-btn':
        card_counter += 1
        new_card = utils.get_new_step_body(card_counter)

        if previous_content is None:
            updated_content = new_card
        else:
            updated_content = previous_content + [new_card, html.P()]
    # if the param file has been added (after button confirmation)
    elif id_ctx == 'confirm-upload':
        if confirm_upload:
            card_counter = 0
            updated_content, card_counter = utils.upload_additional_steps(
                params_file)
        else:  # if the operation is cancelled, do nothing
            updated_content = previous_content
    # if the restore params button has been clicked
    elif id_ctx == 'confirm-reset':
        if confirm_reset:
            updated_content = []
        else:  # if the operation is cancelled, do nothing
            updated_content = previous_content
    # if the remove button is clicked, remove the card
    else:
        remove_idx = id_ctx['index']
        for n, el in enumerate(previous_content):
            prop_idx = el['props']['id']['index']
            if el['type'] == 'Card' and prop_idx == remove_idx:
                del previous_content[n + 1]  # remove the html.P element
                previous_content.remove(el)  # remove the card

        updated_content = previous_content

    return updated_content


# populate the options on the base of the selected processing type
@callback(Output({"type": "additional-step-core", "index": MATCH}, "children"),
          Input({"type": "additional-step-type", "index": MATCH}, "value"),
          State({"type": "additional-step-core", "index": MATCH}, "id"),
          )
def get_body(selected_value, card_id):
    if selected_value in definitions.get_defaults():
        new_section = utils.get_processing_step_layout(card_id, selected_value)
        return new_section
    return []


# download the json file with the processing params and the processed emg
@callback(Output('download-params', 'data'),
          Output('download-emg-processed', 'data'),
          Input('download-data-btn', 'n_clicks'),
          prevent_initial_call=True)
def download_data(click):
    # build the params file
    params_file = {'content': json.dumps(json_parameters),
                   'filename': 'parameters.json'}
    # build the csv file with the processed signal to use the dcc.Download
    # element, we need to convert the np array into a dataframe
    emg_ts = variables.get_emg_timeseries()
    if emg_ts is not None:
        data = emg_ts.to_numpy(signal_io=('env',))
    else:
        data = np.array([])
    df = pd.DataFrame(data.transpose())
    emg_file = dcc.send_data_frame(df.to_csv, 'emg.csv')

    return params_file, emg_file


# expand/shrink raw data column
@callback(Output('raw-signals-column', 'width'),
          Output('processed-signals-column', 'width'),
          Output('collapse-raw', 'is_open'),
          Output('open-column-btn', 'className'),
          Input('open-column-btn', 'n_clicks'),
          State('raw-signals-column', 'width'),
          prevent_initial_call=True)
def open_column(click, current_width):
    if current_width == 1:
        original_width = 4
        processed_width = 6
        open_card = True
        btn_class = "fas fa-angle-right"
    else:
        original_width = 1
        processed_width = 9
        open_card = False
        btn_class = "fas fa-angle-left"

    return original_width, processed_width, open_card, btn_class


# upload json with params
@callback(Output('confirm-upload', 'displayed'),
          Output('alert-invalid-file', 'is_open'),
          Input('upload-processing-params', 'contents'),
          prevent_initial_call=True)
def populate_steps(params_file):
    data = utils.param_file_to_json(params_file)
    # check if the file is correct
    if utils.get_idx_dict_list(data, 'file_identifier', FILE_IDENTIFIER) == 0:
        open_confirmation = True
        open_alert = False
    else:
        open_confirmation = False
        open_alert = True

    return open_confirmation, open_alert


# reset params
@callback(Output('confirm-reset', 'displayed'),
          Input('restore-default-btn', 'n_clicks'),
          prevent_initial_call=True)
def populate_steps(reset_button):
    open_confirmation = True

    return open_confirmation


# # the user confirms the params upload or the reset button is pressed
# @callback(
#         # Output('tail-cut-percent', 'value'),
#         # Output('tail-cut-tolerance', 'value'),
#         # Output('base-filter-low', 'value'),
#         # Output('base-filter-high', 'value'),
#         # Output({"type": "ecg-filter-select", "index": "0"}, 'value'),
#         # Output('envelope-extraction-select', 'value'),
#         Input('confirm-upload', 'submit_n_clicks'),
#         Input('confirm-reset', 'submit_n_clicks'),
#         State('upload-processing-params', 'contents'),
#         prevent_initial_call=True)
# def populate_steps(confirm_upload, confirm_reset, params_file):
#     trigger_id = ctx.triggered_id

#     if ((trigger_id == 'confirm-reset' and confirm_reset)
#           or trigger_id is None):
#         bandpass_low = definitions.default_bandpass_low
#        bandpass_high = utils.check_default_cut_fs(
#            definitions.default_bandpass_high, variables.get_fs_emg())
#         first_cut_percentage = definitions.default_first_cut_percentage
#         first_cut_tolerance = definitions.default_first_cut_tolerance
#         ecg_removal_value = definitions.default_ecg_removal_value
#         envelope_value = definitions.default_envelope_value

#     if trigger_id == 'confirm-upload' and confirm_upload:
#         data = utils.param_file_to_json(params_file)

#         first_cut_percentage = data[1]['percentage']
#         first_cut_tolerance = data[1]['tolerance']
#         bandpass_low = data[2]['low_fs']
#         bandpass_high = data[2]['high_fs']

#         ecg_removal = data[4]['method']
#         ecg_removal_value = utils.get_ecg_removal_value(ecg_removal)

#         envelope = data[-1]['method']
#         envelope_value = utils.get_envelope_method_value(envelope)

#     if confirm_reset or confirm_upload or trigger_id is None:
#         return (first_cut_percentage, first_cut_tolerance, bandpass_low,
#                 bandpass_high, ecg_removal_value, envelope_value)
