import base64
import dash_bootstrap_components as dbc
import definitions
import json
import numpy as np
import plotly.graph_objects as go
import resurfemg.helper_functions as hf
import trace_updater
from dash import dcc, html
from definitions import ProcessTypology, EcgRemovalMethods, EnvelopeMethod, GatingMethod
from plotly_resampler import FigureResampler
from plotly.subplots import make_subplots
from scipy.signal import find_peaks
from typing import Dict
from uuid import uuid4

graph_dict_raw: Dict[str, FigureResampler] = {}

# colors
colors = {
    'white': '#FFFFFF',
    'text': '#091D58',
    'blue1': '#063446',  # dark blue
    'blue2': '#0e749b',
    'blue3': '#15b3f0',
    'blue4': '#E4F3F9',  # light blue
    'yellow1': '#f0d515'
}


# build the layout for emg graphs
def add_emg_graphs(emg_data, fs, titles=None, default_processed=None, units=None):
    if emg_data is None:
        return []

    graphs = []
    show_legend = False

    if emg_data.ndim == 1:
        leads_n = 1
        time_array = get_time_array(emg_data.shape[0], fs)
        if default_processed is not None:
            time_array_processed = get_time_array(
                default_processed.shape[0], fs)
    else:
        leads_n = emg_data.shape[0]
        time_array = get_time_array(emg_data.shape[1], fs)
        if default_processed is not None:
            time_array_processed = get_time_array(
                default_processed.shape[1], fs)

    for i in range(leads_n):

        uid = 'emg' + str(i) + '-graph' + str(uuid4())

        if leads_n == 1:
            y = emg_data
            if default_processed is not None:
                y_default_process = default_processed
        else:
            y = emg_data[i]
            if default_processed is not None:
                y_default_process = default_processed[i]

        fig_title = "EMG Track " + str(i) + ": " + (
            titles[i] if titles is not None else "")

        fig = FigureResampler(
            make_subplots(
                specs=[[{"secondary_y": True}]],
                vertical_spacing=0.1,
                row_heights=[1.0],
            ),
            resampled_trace_prefix_suffix=('', ''),
            show_mean_aggregation_size=False
        )

        if default_processed is not None:
            show_legend = True
            fig.add_trace(go.Scatter(
                name="Default processing",
                opacity=0.7,
                line=dict(
                    color='red',
                    # dash='dot',
                )
            ),
                hf_x=time_array_processed,
                hf_y=np.ascontiguousarray(y_default_process),
            )

        fig.add_trace(go.Scatter(
            name="Current processing",
            opacity=0.5,
            line=dict(
                color='blue',
            )
        ),
            hf_x=time_array,
            hf_y=np.ascontiguousarray(y),
            secondary_y=True
        )

        fig.update_layout(
            xaxis_title="Time [s]",
            yaxis_title=(units[i] if units is not None else "AU"),
            legend_title="Legend",
        )
        fig.update_traces(showlegend=show_legend)
        graphs.append(
            dbc.Switch(
                id={"type": "emg-graph-switch", "index": uid},
                label=fig_title,
                value=True
            ),
        )
        graphs.append(
            dbc.Collapse([
                dcc.Graph(
                    id={"type": "dynamic-graph", "index": uid},
                    figure=fig,
                    config={"displaylogo": False},
                )
            ],
                id={"type": "emg-graph-collapse", "index": uid},
                is_open=True
            )
        )

        graphs.append(trace_updater.TraceUpdater(
            id={"type": "dynamic-updater", "index": uid},
            gdID=uid))

        graph_dict_raw[uid] = fig

    return graphs


# build the layout for ventilator graphs
def add_ventilator_graphs(emg_data, fs, titles=None):
    if emg_data is None:
        return []

    graphs = []
    show_legend = False

    if emg_data.ndim == 1:
        leads_n = 0
        time_array = get_time_array(emg_data.shape[0], fs)
    else:
        leads_n = emg_data.shape[0]
        time_array = get_time_array(emg_data.shape[1], fs)

    for i in range(leads_n):

        uid = 'vent' + str(i) + '-graph' + str(uuid4())

        if leads_n == 0:
            y = emg_data
        else:
            y = emg_data[i]

        if titles is None:
            fig_title = "Ventilator Track " + str(i)
        else:
            fig_title = titles[i]

        fig = FigureResampler(
            make_subplots(
                specs=[[{"secondary_y": True}]],
                vertical_spacing=0.1,
                row_heights=[1.0],
            ),
            resampled_trace_prefix_suffix=('', ''),
            show_mean_aggregation_size=False
        )

        fig.add_trace(go.Scatter(
            name="Ventilator data",
            opacity=0.5,
            line=dict(
                color='blue',
            )
        ),
            hf_x=time_array,
            hf_y=np.ascontiguousarray(y),
        )

        fig.update_layout(
            xaxis_title="Time [s]",
            legend_title="Legend",
        )
        fig.update_traces(showlegend=show_legend)

        graphs.append(
            dbc.Switch(
                id={"type": "emg-graph-switch", "index": uid},
                label=fig_title,
                value=True
            ),
        )
        graphs.append(
            dbc.Collapse([
                dcc.Graph(
                    id={"type": "dynamic-graph", "index": uid},
                    figure=fig,
                    config={"displaylogo": False},
                )
            ],
                id={"type": "emg-graph-collapse", "index": uid},
                is_open=True
            )
        )

        graphs.append(trace_updater.TraceUpdater(
            id={"type": "dynamic-updater", "index": uid},
            gdID=uid))

        graph_dict_raw[uid] = fig

    return graphs


# get the time array, computed from the sampling rate
def get_time_array(data_size, fs):
    time_array = np.arange(0, data_size / fs, 1 / fs)

    return time_array


# function needed to update graphs using plotly_resampler
def get_dict(graph_id_dict, relayoutdata):
    return graph_dict_raw.get(
        graph_id_dict["index"])._construct_update_data(relayoutdata)

def get_graph_fig(dict_key):
    return graph_dict_raw.get(dict_key)

def get_graph_dict():
    return graph_dict_raw


# function needed to update graphs using plotly_resampler
def set_dict(uid, figure):
    graph_dict_raw[uid] = figure


# get the layout for the band pass filter card
def get_band_pass_layout(id_low, id_high, low_value=3, high_value=450):
    layout = [
        dbc.Row([
            dbc.Col([
                html.P("Low cut fs"),
                dcc.Input(
                    id=id_low,
                    type="number",
                    placeholder="low cut",
                    value=low_value
                )
            ]),
            dbc.Col([
                html.P("High cut fs"),
                dcc.Input(
                    id=id_high,
                    type="number",
                    placeholder="high cut",
                    value=high_value
                )
            ])
        ])
    ]

    return layout


# get the layout for the high pass filter card
def get_high_pass_layout(id_low, cut_fs=3):
    layout = [
        dbc.Col([
            html.P("Low cut fs"),
            dcc.Input(
                id=id_low,
                type="number",
                placeholder="low cut",
                value=cut_fs
            )
        ])
    ]

    return layout


# get the layout for the low pass filter card
def get_low_pass_layout(id_low, cut_fs=450):
    layout = [
        dbc.Col([
            html.P("High cut fs"),
            dcc.Input(
                id=id_low,
                type="number",
                placeholder="high cut",
                value=cut_fs
            )
        ])
    ]

    return layout


# get the layout for the ecg removal filter card
def get_ecg_removal_layout(id_removal, value=definitions.default_ecg_removal_value):
    if 'index' in id_removal:
        id_removal_index = id_removal['index']
    else:
        id_removal_index = "0"

    layout = html.Div([dbc.Label("ECG removal method"),
                       dbc.Select(
                           id=id_removal,
                           options=[
                               {"label": "Gating", "value": EcgRemovalMethods.GATING.value},
                               {"label": "None", "value": EcgRemovalMethods.NONE.value},
                           ],
                           value=value
                       )],
                      id={"type": "ecg-removal-card", "index": id_removal_index}
                      )

    return layout


# get the layout fot the new processing step card
def get_new_step_body(index, selected_value="0", core_body=None):
    if core_body is None:
        core_body = []
    new_card = dbc.Card([
        dbc.CardHeader([
            html.Button(
                html.I(className="fas fa-times", style={'color': 'red'}),
                className="ml-auto close",
                id={"type": "step-close-button", "index": str(index)},
                style={'border': 'none',
                       'background': 'transparent'}
            ),
            dbc.Label("Additional step")
        ]),
        dbc.Label("Step type"),
        dbc.Select(
            id={"type": "additional-step-type", "index": str(index)},
            options=[
                {"label": "", "value": "0"},
                {"label": "Band-pass filter", "value": ProcessTypology.BAND_PASS.value},
                {"label": "High-pass filter", "value": ProcessTypology.HIGH_PASS.value},
                {"label": "Low-pass filter", "value": ProcessTypology.LOW_PASS.value},
                {"label": "ECG removal", "value": ProcessTypology.ECG_REMOVAL.value},
            ],
            value=selected_value
        ),
        html.Div(core_body, id={"type": "additional-step-core", "index": str(index)})
    ],
        id={"type": "additional-step-card", "index": str(index)})

    return new_card


def add_gating_method_options(index):
    layout = [
        html.Div([
            dbc.Label("Gating method"),
            dbc.Select(
                id={"type": "gating-method-type", "index": str(index)},
                options=[
                    {"label": "Zero Fill", "value": GatingMethod.ZERO_FILL.value},
                    {"label": "Interpolate", "value": GatingMethod.INTERPOLATE.value},
                    {"label": "Avg. Prior Segment", "value": GatingMethod.AVERAGE_PRIOR_SEGMENT.value},
                    {"label": "Running Avg. RMS", "value": GatingMethod.RUNNING_AVERAGE_RMS.value},
                ],
                value="3"
            )
        ],
            id={"type": "gating-method-div", "index": str(index)})
    ]
    return layout


# get the index of the dict containing the key-value
# in a list of dicts
def get_idx_dict_list(dict_list, key, value):
    idx = next((i for i, item in enumerate(dict_list)
                if item.__contains__(key) and item[key] == value), None)

    return idx


# apply the ecg removal, using the method selected
def apply_ecg_removal(
        removal_method: int, emg_signal, sample_rate, gating_method: int = 3):
    emg_ecg = []
    titles = []

    if removal_method == EcgRemovalMethods.GATING.value:
        # TODO: change with QRS identification when available in library
        peak_width = 0.001
        peak_fraction = 0.40
        ecg_rms = hf.full_rolling_rms(emg_signal[0, :], 10)
        peak_height = peak_fraction * (max(ecg_rms) - min(ecg_rms))
        ecg_peaks, _ = find_peaks(ecg_rms,
                                  height=peak_height,
                                  width=peak_width * sample_rate,
                                  distance=int(sample_rate / 3))

        titles.append("Filtered Track 0")
        for lead in range(1, emg_signal.shape[0]):
            emg_clean = hf.gating(emg_signal[lead, :], ecg_peaks, method=gating_method)
            emg_ecg.append(emg_clean)
            titles.append("Filtered Track " + str(lead))

        emg_ecg = np.array(emg_ecg)
        emg_ecg = np.insert(emg_ecg, 0, emg_signal[0], 0)

    else:
        emg_ecg = emg_signal
        titles = None

    return emg_ecg, titles


# build the json containing the params for the cutter
def build_cutter_params_json(step_number: int, percentage: int, tolerance: int):
    data = {
        'step_number': step_number,
        'step_type': ProcessTypology.CUT.name,
        'percentage': percentage,
        'tolerance': tolerance
    }

    return data


# build the json containing the params for the band pass filter
def build_bandpass_params_json(step_number: int, low_fs: int, high_fs: int):
    data = {
        'step_number': step_number,
        'step_type': ProcessTypology.BAND_PASS.name,
        'low_fs': low_fs,
        'high_fs': high_fs
    }

    return data


# build the json containing the params for the high pass filter
def build_highpass_params_json(step_number: int, cut_fs: int):
    data = {
        'step_number': step_number,
        'step_type': ProcessTypology.HIGH_PASS.name,
        'cut_fs': cut_fs
    }

    return data


# build the json containing the params for the low pass filter
def build_lowpass_params_json(step_number: int, cut_fs: int):
    data = {
        'step_number': step_number,
        'step_type': ProcessTypology.LOW_PASS.name,
        'cut_fs': cut_fs
    }

    return data


# build the json containing the params for the ecg removal
def build_ecgfilt_params_json(step_number: int, method: EcgRemovalMethods, gating_method: GatingMethod = None):
    data = {
        'step_number': step_number,
        'step_type': ProcessTypology.ECG_REMOVAL.name,
        'method': method.name
    }

    if gating_method is not None:
        data['gating_method'] = gating_method.name

    return data


# build the json containing the params for the envelope extraction
def build_envelope_params_json(step_number: int, method: EnvelopeMethod):
    data = {
        'step_number': step_number,
        'step_type': ProcessTypology.ENVELOPE.name,
        'method': method.name
    }

    return data


def get_ecg_removal_value(method_name):
    ecg_removal_value = 0

    for ecg_method in EcgRemovalMethods:
        if method_name == ecg_method.name:
            ecg_removal_value = ecg_method.value

    return ecg_removal_value


def get_envelope_method_value(method_name):
    envelope_value = 0

    for envelope_method in EnvelopeMethod:
        if method_name == envelope_method.name:
            envelope_value = envelope_method.value

    return envelope_value


def param_file_to_json(param_file):
    content_type, content_string = param_file.split(',')
    decoded = base64.b64decode(content_string).decode('utf8')
    data = json.loads(decoded)

    return data


def upload_additional_steps(params_file):
    core_body = []
    card_counter_local = 0

    data = param_file_to_json(params_file)

    for steps_index in range(5, len(data) - 1):
        step_type = data[steps_index]['step_type']
        card_counter_local += 1
        if step_type == ProcessTypology.BAND_PASS.name:
            new_card = get_band_pass_layout({"type": "additional-step-low", "index": str(card_counter_local)},
                                            {"type": "additional-step-high", "index": str(card_counter_local)},
                                            data[steps_index]['low_fs'],
                                            data[steps_index]['high_fs'])
            list_value = ProcessTypology.BAND_PASS.value
        elif step_type == ProcessTypology.HIGH_PASS.name:
            new_card = get_high_pass_layout({"type": "additional-step-low", "index": str(card_counter_local)},
                                            data[steps_index]['cut_fs'])
            list_value = ProcessTypology.HIGH_PASS.value
        elif step_type == ProcessTypology.LOW_PASS.name:
            new_card = get_high_pass_layout({"type": "additional-step-high", "index": str(card_counter_local)},
                                            data[steps_index]['cut_fs'])
            list_value = ProcessTypology.LOW_PASS.value
        elif step_type == ProcessTypology.ECG_REMOVAL.name:
            ecg_removal_value = get_ecg_removal_value(data[steps_index]['method'])
            new_card = get_ecg_removal_layout({"type": "additional-step-removal", "index": str(card_counter_local)},
                                              data[steps_index]['method'])
            list_value = ProcessTypology.ECG_REMOVAL.value

        steps_body = get_new_step_body(card_counter_local, list_value, new_card)
        core_body = core_body + [steps_body, html.P()]

    return core_body, card_counter_local


def check_default_cut_fs(default_fs: int, sampling_rate: int) -> int:
    # check compatibility of the base filter upper cut fs
    # if the sampling fs is lower than twice the default value
    # we need to adjust it

    high_cut = default_fs

    if sampling_rate is None:
        return default_fs

    if default_fs > sampling_rate/2:
        # -1 because the butter filter fails if the cut-off fs
        # is equal to half the sampling rate

        high_cut = int(sampling_rate / 2) - 1

    return high_cut
