"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

import dash
import definitions
import json
import numpy as np
import pandas as pd
import utils
from app import variables
from dash import Input, Output, State, callback, MATCH, ALL, html, ctx, dcc
from definitions import ProcessTypology, EcgRemovalMethods, EnvelopeMethod, FILE_IDENTIFIER, GatingMethod
from resurfemg.data_connector.data_classes import EmgDataGroup

card_counter = 0
json_parameters = []

# inspect.getfullargspec(TimeSeries)
# inspect.getmembers(TimeSeries, predicate=inspect.isfunction)

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
        #   State('base-filter-low', 'value'),
        #   State('base-filter-high', 'value'),
        #   State({"type": "ecg-filter-select", "index": "0"}, "value"),
        #   State('envelope-extraction-select', 'value'),
          State({"type": "additional-step-core", "index": ALL}, "id"),
          State({"type": "additional-step-type", "index": ALL}, "value"),
          State({"type": "additional-step-core", "index": ALL}, "children"),
        #   State({"type": "additional-step-low", "index": ALL}, "value"),
        #   State({"type": "additional-step-low", "index": ALL}, "id"),
        #   State({"type": "additional-step-high", "index": ALL}, "value"),
        #   State({"type": "additional-step-high", "index": ALL}, "id"),
        #   State({"type": "ecg-filter-select", "index": ALL}, "value"),
        #   State({"type": "ecg-filter-select", "index": ALL}, "id"),
        #   State({"type": "gating-method-type", "index": ALL}, "value"),
        #   State({"type": "gating-method-type", "index": ALL}, "id")
        )
def show_data(click,
            #   low_freq,
            #   high_freq_default,
            #   ecg_method,
            #   envelope_method,
              additional_card,
              additional_steps,
              additional_steps_args,
            #   additional_low,
            #   additional_low_idx,
            #   additional_high,
            #   additional_high_idx,
            #   additional_rem,
            #   additional_rem_idx,
            #   gating_method,
            #   gating_method_idx
              ):
    # variables initialization
    global json_parameters

    # Reset the list of processing steps parameters
    json_parameters.clear()
    # Added to easily verify the file compatibility when uploaded
    json_parameters.append({'file_identifier': FILE_IDENTIFIER})

    emg_data = variables.get_emg()
    emg_ts = variables.get_emg_timeseries()
    fs = variables.get_emg_freq()

    # # we have to make sure that the cut-off frequencies are in an acceptable range
    # high_freq = utils.check_default_cut_fs(high_freq_default, fs)
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

    if trigger is not None:
        # Process the set processing pipeline
        sel_opts = {}
        for n, card in enumerate(additional_card):
            card_id = int(card['index'])
            sel_opts[card_id] = {}
            sel_opts[card_id]['method'] = additional_steps[n]
            sel_opts[card_id]['args_val'] = {}
            for item in additional_steps_args[n]:
                arg_id = item['props']['children'][1]['props']['id']['type']
                if arg_id.startswith('processing-step-'):
                    arg_name = item['props']['children'][1]['props']['name']
                    arg_value = item['props']['children'][1]['props']['value']
                    sel_opts[card_id]['args_val'][arg_name] = arg_value
            default_settings = definitions.get_defaults(
                sel_opts[card_id]['method'])
            # Assure adequate type for the arguments
            def_args = default_settings['arg_defaults']
            for arg_name, arg_value in def_args.items():
                if arg_name in sel_opts[card_id]['args_val']:
                    if isinstance(arg_value, int):
                        sel_opts[card_id]['args_val'][arg_name] = int(
                            sel_opts[card_id]['args_val'][arg_name])
                    elif isinstance(arg_value, float):
                        sel_opts[card_id]['args_val'][arg_name] = float(
                            sel_opts[card_id]['args_val'][arg_name])
                    elif isinstance(arg_value, str):
                        sel_opts[card_id]['args_val'][arg_name] = str(
                            sel_opts[card_id]['args_val'][arg_name].lower())
            set_args = default_settings['set_args']
            for arg_name in set_args:
                sel_opts[card_id]['args_val'][arg_name] = set_args[arg_name]
        custom_pipeline = def_opts != sel_opts
    else:
        custom_pipeline = False
        

    # if data have been loaded, apply the processing
    if emg_data is not None:
        # apply cut
        # emg_cut = hf.bad_end_cutter_for_samples(emg_data, cut_percent, cut_tolerance)
        # json_parameters.append(utils.build_cutter_params_json(1, cut_percent, cut_tolerance))
        ecg_removal_methods = definitions.ecg_removal_methods
        ecg_rem_counter = 0
        for i, options in def_opts.items():
            method = options['method']
            if method in ecg_removal_methods:
                ecg_peakset_name = 'ecg_' + str(ecg_rem_counter)
                emg_ts.run('get_ecg_peaks',
                                   name=ecg_peakset_name,
                                   overwrite=True)
                options['args_val']['ecg_peakset_name'] = ecg_peakset_name
                ecg_rem_counter += 1
            emg_ts.run(method, **options['args_val'])

        preprocessed_def = np.array([ts.y_clean for ts in emg_ts])
        emg_env = np.array([ts.y_env for ts in emg_ts])

        variables.set_emg_processed_default(preprocessed_def)
        variables.set_emg_processed(emg_env)
        variables.set_emg_timeseries(emg_ts)

        titles = [ts.label for ts in emg_ts]
        units = [ts.y_units for ts in emg_ts]
        preprocessed_def = variables.get_emg_processed_default()

        plot_data, plot_info = utils.update_plot_data(
            new_data=emg_data,
            new_info={'signal':'Raw', 'color':'black', 'secondary':True,
                      'visible': 'legendonly'},
        )
        plot_data, plot_info = utils.update_plot_data(
            new_data=preprocessed_def,
            new_info={'signal':'Filtered', 'color':'blue', 'secondary':False,
                      'visible': 'legendonly' if custom_pipeline else True},
            prev_data=plot_data, prev_info=plot_info
        )
        plot_data, plot_info = utils.update_plot_data(
            new_data=emg_env,
            new_info={'signal':'Envelope', 'color':'red', 'secondary':False,
                      'visible': 'legendonly' if custom_pipeline else True},
            prev_data=plot_data, prev_info=plot_info
        )
        fs = emg_ts.param['fs'] if 'fs' in emg_ts.param else None

        if custom_pipeline:
            emg_raw = np.array([ts.y_raw for ts in emg_ts])
            emg_ts_custom = EmgDataGroup(
                emg_raw, fs=fs, labels=titles, units=units)
            ecg_rem_counter = 0
            for i, options in sel_opts.items():
                method = options['method']
                if method in ecg_removal_methods:
                    ecg_peakset_name = 'ecg_' + str(ecg_rem_counter)
                    emg_ts_custom.run('get_ecg_peaks',
                                    name=ecg_peakset_name,
                                    overwrite=True)
                    options['args_val']['ecg_peakset_name'] = ecg_peakset_name
                    ecg_rem_counter += 1
                emg_ts_custom.run(method, **options['args_val'])

            preprocessed_def = np.array([ts.y_clean for ts in emg_ts_custom])
            emg_env = np.array([ts.y_env for ts in emg_ts_custom])
            plot_data, plot_info = utils.update_plot_data(
                new_data=preprocessed_def,
                new_info={
                    'signal':'Filtered (custom)', 'color':'cyan',
                    'secondary':False,
                    'visible': True},
                prev_data=plot_data, prev_info=plot_info
            )
            plot_data, plot_info = utils.update_plot_data(
                new_data=emg_env,
                new_info={
                    'signal':'Envelope (custom)', 'color':'orange',
                    'secondary':False,
                    'visible': True},
                prev_data=plot_data, prev_info=plot_info
            )


        # emg_ts.run('filter_emg')
        # emg_ts.run('get_ecg_peaks', overwrite=True)
        # emg_ts.run('gating')
        # emg_ts.run('envelope')
        
        

        
        
        # new_step_emg = np.array([ts.y_clean for ts in emg_ts])
        # # get the custom steps added, and apply the selected processing
            # for n, card in enumerate(additional_card):
            #     card_id = card['index']
            #     step = additional_steps[n]
            #     print(f'Processing step {n}: {step}')
            #     print(additional_steps_args[n])
        #     if step == ProcessTypology.BAND_PASS.value:
        #         idx_low = utils.get_idx_dict_list(
        #             additional_low_idx, 'index', card_id)
        #         idx_high = utils.get_idx_dict_list(
        #             additional_high_idx, 'index', card_id)

        #         low_cut = additional_low[idx_low]
        #         high_cut_input = additional_high[idx_high]
        #         high_cut = utils.check_default_cut_fs(
        #             high_cut_input, fs)

        #         new_step_emg = filt.emg_bandpass_butter(
        #             new_step_emg, high_pass=low_cut, low_pass=high_cut,
        #             fs_emg=fs)
        #         json_parameters.append(utils.build_bandpass_params_json(
        #             len(json_parameters) + 1, low_cut, high_cut))

        #     elif step == ProcessTypology.HIGH_PASS.value:
        #         idx = utils.get_idx_dict_list(
        #             additional_low_idx, 'index', card_id)
        #         low_cut = additional_low[idx]

        #         new_step_emg = filt.emg_highpass_butter(
        #             new_step_emg, high_pass=low_cut, fs_emg=fs)
        #         json_parameters.append(utils.build_highpass_params_json(
        #             len(json_parameters) + 1, low_cut))

        #     elif step == ProcessTypology.LOW_PASS.value:
        #         idx = utils.get_idx_dict_list(
        #             additional_high_idx, 'index', card_id)

        #         high_cut_input = additional_high[idx]
        #         high_cut = utils.check_default_cut_fs(
        #             high_cut_input, fs)

        #         # TODO: add function when it will be available in helper_functions
        #         new_step_emg = filt.emg_lowpass_butter(
        #             new_step_emg, low_cut, fs)
        #         json_parameters.append(utils.build_lowpass_params_json(
        #             n + 5, high_cut))

        #     elif step == ProcessTypology.ECG_REMOVAL.value:
        #         idx = utils.get_idx_dict_list(
        #             additional_rem_idx, 'index', card_id) - 1

        #         ecg_additional_method = additional_rem[idx]
        #         if ecg_additional_method == EcgRemovalMethods.GATING.value:
        #             gating_method_type = int(gating_method[idx])
        #             json_parameters.append(utils.build_ecgfilt_params_json(
        #                 len(json_parameters) + 1,
        #                 EcgRemovalMethods(ecg_additional_method),
        #                 GatingMethod(gating_method[idx])
        #             ))
        #         else:
        #             gating_method_type = None
        #             json_parameters.append(utils.build_ecgfilt_params_json(
        #                 len(json_parameters) + 1,
        #                 EcgRemovalMethods(ecg_additional_method)
        #             ))

        #         # at the moment we need to create a matrix with 3 leads to use the methods
        #         # the lead 0 is the  ecg lead, the other two are the same processed signal
        #         # if the matrix is still bi-dimensional, we use it

        #         if new_step_emg.ndim == 1:
        #             tmp_matrix = np.array([emg_cut_final[0, :],
        #                                    new_step_emg,
        #                                    new_step_emg])
        #         else:
        #             tmp_matrix = new_step_emg

        #         new_step_emg, titles = utils.apply_ecg_removal(
        #             ecg_additional_method,
        #             tmp_matrix,
        #             fs,
        #             gating_method_type)



        # # if the processing is the default one, store it (TODO: FIX
        # store the processed signal
        

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
def add_step(click, close, confirm_upload, confirm_reset, params_file, previous_content):
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

#     if (trigger_id == 'confirm-reset' and confirm_reset) or trigger_id is None:
#         bandpass_low = definitions.default_bandpass_low
#         bandpass_high = utils.check_default_cut_fs(definitions.default_bandpass_high,
#                                                           variables.get_emg_freq())
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
#         return first_cut_percentage, first_cut_tolerance, bandpass_low, bandpass_high, ecg_removal_value, envelope_value


# # populate the options on the base of the selected processing type
# @callback(Output({"type": "ecg-removal-card", "index": MATCH}, "children"),
#           Input({"type": "ecg-filter-select", "index": MATCH}, "value"),
#           State({"type": "ecg-removal-card", "index": MATCH}, "children"),
#           State({"type": "ecg-removal-card", "index": MATCH}, "id"),
#           prevent_initial_call=True)
# def get_body(selected_value, container, id_origin):
#     if selected_value == EcgRemovalMethods.GATING.value:
#         new_section = container + utils.add_gating_method_options(id_origin["index"])
#     else:
#         for element in container:
#             if 'id' in element['props'] and element['props']['id']['type'] == 'gating-method-div':
#                 container.remove(element)
#         new_section = container
#     return new_section
