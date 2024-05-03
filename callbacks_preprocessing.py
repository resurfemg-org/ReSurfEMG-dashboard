"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

import dash
from resurfemg.preprocessing import filtering as filt
import definitions
import json
import numpy as np
import pandas as pd
import utils

from app import variables
from dash import Input, Output, State, callback, MATCH, ALL, html, ctx, dcc
from definitions import ProcessTypology, EcgRemovalMethods, EnvelopeMethod, FILE_IDENTIFIER, GatingMethod
#from resurfemg import helper_functions as hf


card_counter = 0
json_parameters = []


# on loading add the emg graphs
@callback(Output('preprocessing-original-container', 'children'),
          Output('emg-filename-preprocessing', 'children'),
          Input('load-preprocessing-div', 'data'))
def show_raw_data(data):
    global card_counter

    emg_data = variables.get_emg()
    emg_frequency = variables.get_emg_freq()
    filename = variables.get_emg_filename()

    if emg_data is not None:
        children_emg = utils.add_emg_graphs(np.array(emg_data), emg_frequency)
    else:
        children_emg = []

    return children_emg, filename


# apply the processing on the button click
@callback(Output('preprocessing-processed-container', 'children'),
          Output('download-data-btn', 'disabled'),
          Input('apply-pipeline-btn', 'n_clicks'),
          State('tail-cut-percent', 'value'),
          State('tail-cut-tolerance', 'value'),
          State('base-filter-low', 'value'),
          State('base-filter-high', 'value'),
          State({"type": "ecg-filter-select", "index": "0"}, "value"),
          State('envelope-extraction-select', 'value'),
          State({"type": "additional-step-core", "index": ALL}, "id"),
          State({"type": "additional-step-type", "index": ALL}, "value"),
          State({"type": "additional-step-low", "index": ALL}, "value"),
          State({"type": "additional-step-low", "index": ALL}, "id"),
          State({"type": "additional-step-high", "index": ALL}, "value"),
          State({"type": "additional-step-high", "index": ALL}, "id"),
          State({"type": "ecg-filter-select", "index": ALL}, "value"),
          State({"type": "ecg-filter-select", "index": ALL}, "id"),
          State({"type": "gating-method-type", "index": ALL}, "value"),
          State({"type": "gating-method-type", "index": ALL}, "id"))
def show_data(click,
              cut_percent,
              cut_tolerance,
              low_freq,
              high_freq_default,
              ecg_method,
              envelope_method,
              additional_card,
              additional_steps,
              additional_low,
              additional_low_idx,
              additional_high,
              additional_high_idx,
              additional_rem,
              additional_rem_idx,
              gating_method,
              gating_method_idx):
    # variables initialization
    global json_parameters

    # Reset the list of processing steps parameters
    json_parameters.clear()
    # Added to easily verify the file compatibility when uploaded
    json_parameters.append({'file_identifier': FILE_IDENTIFIER})

    emg_data = variables.get_emg()
    sample_rate = variables.get_emg_freq()

    # we have to make sure that the cut-off frequencies are in an acceptable range
    high_freq = utils.check_default_cut_frequency(high_freq_default, sample_rate)

    # if data have been loaded, apply the processing
    if emg_data is not None:
        # apply cut
        emg_cut = filt.bad_end_cutter_for_samples(emg_data, cut_percent, cut_tolerance)
        json_parameters.append(utils.build_cutter_params_json(1, cut_percent, cut_tolerance))

        # apply filter
        emg_data_filtered = filt.emg_bandpass_butter_sample(emg_cut,
                                                          low_freq,
                                                          high_freq,
                                                          sample_rate)
        json_parameters.append(utils.build_bandpass_params_json(2, low_freq, high_freq))

        # remove filtering artifacts (this is done automatically, no params are
        # displayed in the GUI
        emg_cut_final = filt.bad_end_cutter_for_samples(emg_data_filtered, 3, 5)
        json_parameters.append(utils.build_cutter_params_json(3, 3, 5))

        # remove ECG
        if ecg_method == EcgRemovalMethods.GATING.value:
            gating_method_default_idx = utils.get_idx_dict_list(gating_method_idx, 'index', '0')
            gating_method_default = int(gating_method[gating_method_default_idx])
            json_parameters.append(utils.build_ecgfilt_params_json(4,
                                                                   EcgRemovalMethods(ecg_method),
                                                                   GatingMethod(
                                                                       gating_method[gating_method_default_idx])))
        else:
            gating_method_default = None
            json_parameters.append(utils.build_ecgfilt_params_json(4, EcgRemovalMethods(ecg_method)))

        emg_ecg, titles = utils.apply_ecg_removal(ecg_method, emg_cut_final, sample_rate, gating_method_default)

        new_step_emg = emg_ecg

        # get the custom steps added, and apply the selected processing
        for n, card in enumerate(additional_card):
            card_id = card['index']
            step = additional_steps[n]
            if step == ProcessTypology.BAND_PASS.value:
                idx_low = utils.get_idx_dict_list(additional_low_idx, 'index', card_id)
                idx_high = utils.get_idx_dict_list(additional_high_idx, 'index', card_id)

                low_cut = additional_low[idx_low]
                high_cut_input = additional_high[idx_high]
                high_cut = utils.check_default_cut_frequency(high_cut_input, sample_rate)

                new_step_emg = filt.emg_bandpass_butter_sample(new_step_emg,
                                                             low_cut, high_cut,
                                                             sample_rate)
                json_parameters.append(utils.build_bandpass_params_json(len(json_parameters) + 1,
                                                                        low_cut,
                                                                        high_cut))

            elif step == ProcessTypology.HIGH_PASS.value:
                idx = utils.get_idx_dict_list(additional_low_idx, 'index', card_id)
                low_cut = additional_low[idx]

                new_step_emg = filt.emg_highpass_butter(new_step_emg,
                                                      low_cut,
                                                      sample_rate)
                json_parameters.append(utils.build_highpass_params_json(len(json_parameters) + 1,
                                                                        low_cut))

            elif step == ProcessTypology.LOW_PASS.value:
                idx = utils.get_idx_dict_list(additional_high_idx, 'index', card_id)

                high_cut_input = additional_high[idx]
                high_cut = utils.check_default_cut_frequency(high_cut_input, sample_rate)

                # TODO: add function when it will be available in helper_functions
                # new_step_emg = hf.emg_lowpass_butter(new_step_emg, low_cut, sample_rate)
                # json_parameters.append(utils.build_lowpass_params_json(n + 5, high_cut))

            elif step == ProcessTypology.ECG_REMOVAL.value:
                idx = utils.get_idx_dict_list(additional_rem_idx, 'index', card_id) - 1

                ecg_additional_method = additional_rem[idx]
                if ecg_additional_method == EcgRemovalMethods.GATING.value:
                    gating_method_type = int(gating_method[idx])
                    json_parameters.append(utils.build_ecgfilt_params_json(len(json_parameters) + 1,
                                                                           EcgRemovalMethods(ecg_additional_method),
                                                                           GatingMethod(gating_method[idx])
                                                                           ))
                else:
                    gating_method_type = None
                    json_parameters.append(utils.build_ecgfilt_params_json(len(json_parameters) + 1,
                                                                           EcgRemovalMethods(ecg_additional_method)
                                                                           ))

                # at the moment we need to create a matrix with 3 leads to use the methods
                # the lead 0 is the  ecg lead, the other two are the same processed signal
                # if the matrix is still bi-dimensional, we use it

                if new_step_emg.ndim == 1:
                    tmp_matrix = np.array([emg_cut_final[0, :], new_step_emg, new_step_emg])
                else:
                    tmp_matrix = new_step_emg

                new_step_emg, titles = utils.apply_ecg_removal(ecg_additional_method,
                                                               tmp_matrix,
                                                               sample_rate,
                                                               gating_method_type)

        # At the end, extract the envelope
        emg_env = utils.get_envelope(envelope_method, new_step_emg, sample_rate)
        json_parameters.append(utils.build_envelope_params_json(len(json_parameters) + 1,
                                                                EnvelopeMethod(envelope_method)
                                                                ))

        # store the processed signal
        variables.set_emg_processed(emg_env)
        # if the processing is the default one, store it
        if ctx.triggered_id != 'apply-pipeline-btn':
            preprocessed_def = np.insert(emg_env, 0, emg_cut_final[0], 0)
            variables.set_emg_processed_default(preprocessed_def)
        # update the graphs

        leads_displayed = emg_env.shape[0]
        preprocessed_def = variables.get_emg_processed_default()
        if leads_displayed != preprocessed_def.shape[0]:
            # in case the dimension is different, the ecg lead is not included
            preprocessed_def = preprocessed_def[1:leads_displayed + 1, :]

        children_emg = utils.add_emg_graphs(emg_env,
                                            sample_rate,
                                            titles,
                                            preprocessed_def)
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
def add_step(click, close, confirm_upload, confirm_reset, params_file, previous_content):
    global card_counter

    id_ctx = ctx.triggered_id
    # if the page is reloaded the steps are reset
    if id_ctx is None:
        card_counter = 0
        return []
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
            updated_content, card_counter = utils.upload_additional_steps(params_file)
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
            if el['type'] == 'Card' and el['props']['id']['index'] == remove_idx:
                del previous_content[n + 1]  # remove the html.P element
                previous_content.remove(el)  # remove the card

        updated_content = previous_content

    return updated_content


# populate the options on the base of the selected processing type
@callback(Output({"type": "additional-step-core", "index": MATCH}, "children"),
          Input({"type": "additional-step-type", "index": MATCH}, "value"),
          State({"type": "additional-step-core", "index": MATCH}, "id"),
          prevent_initial_call=True)
def get_body(selected_value, card_id):
    new_section = []
    if selected_value == ProcessTypology.BAND_PASS.value:
        new_section = utils.get_band_pass_layout({"type": "additional-step-low", "index": card_id['index']},
                                                 {"type": "additional-step-high", "index": card_id['index']})
    elif selected_value == ProcessTypology.HIGH_PASS.value:
        new_section = utils.get_high_pass_layout({"type": "additional-step-low", "index": card_id['index']})
    elif selected_value == ProcessTypology.LOW_PASS.value:
        new_section = utils.get_low_pass_layout({"type": "additional-step-high", "index": card_id['index']})
    elif selected_value == ProcessTypology.ECG_REMOVAL.value:
        new_section = utils.get_ecg_removal_layout({"type": "ecg-filter-select", "index": card_id['index']})

    return new_section


# download the json file with the processing params and the processed emg
@callback(Output('download-params', 'data'),
          Output('download-emg-processed', 'data'),
          Input('download-data-btn', 'n_clicks'),
          prevent_initial_call=True)
def download_data(click):
    # build the params file
    params_file = dict(content=json.dumps(json_parameters), filename='parameters.json')

    # build the csv file with the processed signal
    # to use the dcc.Download element, we need to convert the np array into a dataframe
    df = pd.DataFrame(variables.get_emg_processed().transpose())
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


# the user confirms the params upload or the reset button is pressed
@callback(Output('tail-cut-percent', 'value'),
          Output('tail-cut-tolerance', 'value'),
          Output('base-filter-low', 'value'),
          Output('base-filter-high', 'value'),
          Output({"type": "ecg-filter-select", "index": "0"}, 'value'),
          Output('envelope-extraction-select', 'value'),
          Input('confirm-upload', 'submit_n_clicks'),
          Input('confirm-reset', 'submit_n_clicks'),
          State('upload-processing-params', 'contents'),
          prevent_initial_call=True)
def populate_steps(confirm_upload, confirm_reset, params_file):
    trigger_id = ctx.triggered_id

    if (trigger_id == 'confirm-reset' and confirm_reset) or trigger_id is None:
        bandpass_low = definitions.default_bandpass_low
        bandpass_high = utils.check_default_cut_frequency(definitions.default_bandpass_high,
                                                          variables.get_emg_freq())
        first_cut_percentage = definitions.default_first_cut_percentage
        first_cut_tolerance = definitions.default_first_cut_tolerance
        ecg_removal_value = definitions.default_ecg_removal_value
        envelope_value = definitions.default_envelope_value

    if trigger_id == 'confirm-upload' and confirm_upload:
        data = utils.param_file_to_json(params_file)

        first_cut_percentage = data[1]['percentage']
        first_cut_tolerance = data[1]['tolerance']
        bandpass_low = data[2]['low_frequency']
        bandpass_high = data[2]['high_frequency']

        ecg_removal = data[4]['method']
        ecg_removal_value = utils.get_ecg_removal_value(ecg_removal)

        envelope = data[-1]['method']
        envelope_value = utils.get_envelope_method_value(envelope)

    if confirm_reset or confirm_upload or trigger_id is None:
        return first_cut_percentage, first_cut_tolerance, bandpass_low, bandpass_high, ecg_removal_value, envelope_value


# populate the options on the base of the selected processing type
@callback(Output({"type": "ecg-removal-card", "index": MATCH}, "children"),
          Input({"type": "ecg-filter-select", "index": MATCH}, "value"),
          State({"type": "ecg-removal-card", "index": MATCH}, "children"),
          State({"type": "ecg-removal-card", "index": MATCH}, "id"),
          prevent_initial_call=True)
def get_body(selected_value, container, id_origin):
    if selected_value == EcgRemovalMethods.GATING.value:
        new_section = container + utils.add_gating_method_options(id_origin["index"])
    else:
        for element in container:
            if 'id' in element['props'] and element['props']['id']['type'] == 'gating-method-div':
                container.remove(element)
        new_section = container
    return new_section
