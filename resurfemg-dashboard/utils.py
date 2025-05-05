import base64
import dash_bootstrap_components as dbc
import definitions
import json
import numpy as np
import plotly.graph_objects as go
import trace_updater
from dash import dcc, html
from definitions import processing_methods, get_defaults, ProcessTypology
from plotly_resampler import FigureResampler
from plotly.subplots import make_subplots
from typing import Dict
from uuid import uuid4

graph_dict_raw: Dict[str, FigureResampler] = {}

# colors
colors = {
    'white': '#FFFFFF',
    'text': '#091D58',
    'blue1': '#000080',  # dark blue
    'blue2': '#0e749b',
    'blue3': '#15b3f0',
    'blue4': '#E4F3F9',  # light blue
    'yellow1': '#f0d515'
}


def update_plot_data(new_data, new_info, prev_data=None, prev_info=None):
    if prev_data is None:
        n_dim = new_data.ndim
        n_samp = new_data.shape[0] if n_dim == 1 else new_data.shape[1]
        n_ch = new_data.shape[0] if n_dim > 1 else 1
        plot_data = np.reshape(new_data, (n_ch, n_samp, 1))
    else:
        _new_data = np.expand_dims(new_data, axis=2)
        plot_data = np.concatenate((prev_data, _new_data), axis=2)

    if prev_info is None:
        plot_info = []
    else:
        plot_info = prev_info.copy()
    plot_info.append(new_info)

    return plot_data, plot_info


def add_emg_graphs(plot_data, plot_info, fs, titles=None, units=None):
    """build the layout for emg graphs"""
    if plot_data is None:
        return []

    graphs = []
    show_legend = False
    leads_n = plot_data.shape[0]
    time_array = get_time_array(plot_data.shape[1], fs)

    for i in range(leads_n):
        uid = 'emg' + str(i) + '-graph' + str(uuid4())
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
        if plot_data.shape[2] > 1:
            show_legend = True
        for j in range(plot_data.shape[2]):
            fig.add_trace(go.Scatter(
                name=plot_info[j]['signal'],
                opacity=0.5,
                line=dict(
                    color=plot_info[j]['color'],
                    # dash='dot',
                ),
                visible=plot_info[j]['visible'],
            ),
                hf_x=time_array,
                hf_y=np.ascontiguousarray(plot_data[i, :, j]),
                secondary_y=plot_info[j]['secondary'],
            )

        fig.update_layout(
            xaxis_title="Time [s]",
            yaxis_title=f'{titles[i]} ({units[i]})',
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
def add_ventilator_graphs(plot_data, plot_info, fs, titles=None, units=None):
    if plot_data is None:
        return []

    graphs = []
    show_legend = False
    leads_n = plot_data.shape[0]
    time_array = get_time_array(plot_data.shape[1], fs)

    for i in range(leads_n):
        uid = 'vent' + str(i) + '-graph' + str(uuid4())
        fig_title = "Ventilator Track " + str(i) + ": " + (
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
        if plot_data.shape[2] > 1:
            show_legend = True
        for j in range(plot_data.shape[2]):
            fig.add_trace(go.Scatter(
                name=plot_info[j]['signal'],
                opacity=0.5,
                line=dict(
                    color=plot_info[j]['color'],
                    # dash='dot',
                ),
                visible=plot_info[j]['visible'],
            ),
                hf_x=time_array,
                hf_y=np.ascontiguousarray(plot_data[i, :, j]),
                secondary_y=plot_info[j]['secondary'],
            )

        fig.update_layout(
            xaxis_title="Time [s]",
            yaxis_title=f'{titles[i]} ({units[i]})',
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


def format_option(option):
    if isinstance(option, str):
        replacements = {
            "_samples": " (samples)", "_s": " (samples)",
            "hp_cf": "High pass cut-off", "lp_cf": "Low pass cut-off",
            "_": " ",
        }
        for old, new in replacements.items():
            option = option.replace(old, new)
        option = option.capitalize()
        all_caps_words = ['emg', 'ecg', 'rms', 'arv']
        for word in all_caps_words:
            option = option.replace(word, word.upper())
            option = option.replace(word.capitalize(), word.upper())
        return option
    if isinstance(option, int):
        return str(option)
    if isinstance(option, float):
        return "{:.1f}".format(option)
    return option


def get_processing_step_layout(card_id, method, fs=2048, values=None):
    """get auto generated layout for processing steps"""
    layout = []
    options = get_defaults(method, fs) or processing_methods[method]
    for option in options['arg_defaults']:
        option_id = {"type": "processing-step-" + option,
                     "index": card_id}
        var_options = {}
        if isinstance(values, dict) and option in values:
            set_value = values[option]
        else:
            set_value = options['arg_defaults'][option]

        if isinstance(options['arg_options'][option], tuple):
            var_options.update({k: v for k, v in zip(
                ['min', 'max', 'step'],
                options['arg_options'][option]) if v is not None})
            layout.append(
                dbc.Col([
                    html.P(format_option(option)),
                    dcc.Input(
                        id=option_id,
                        name=option,
                        type="number",
                        value=set_value,
                        placeholder=option.replace("_", " ").capitalize(),
                        min=var_options.get('min', None),
                        max=var_options.get('max', None),
                        step=var_options.get('step', None),
                        style={"width": "100%"}
                    )
                ])
            )
        elif isinstance(options['arg_options'][option], dict):
            var_options = {
                'options': options['arg_options'][option]
            }
            layout.append(
                dbc.Col([
                    html.P(format_option(option)),
                    dbc.Select(
                        id=option_id,
                        name=option,
                        options=[
                            {"label": format_option(value),
                             "value": key} for key, value in
                            var_options['options'].items()
                        ],
                        value=set_value,
                        style={"width": "100%"}
                    )
                ])
            )

    return layout


# get the layout fot the new processing step card
def get_new_step_body(index, default=False, core_body=None, method=None):
    if core_body is None:
        core_body = []
    methods = get_defaults()
    if default:
        header = dbc.Col(
            dbc.Select(
                id={"type": "additional-step-type",
                    "index": str(index)},
                options=[
                    {"label": format_option(key), "value": key}
                    for key in methods
                ],
                value=method,
                placeholder="Step type",
                style={'width': '100%'},
                disabled=True
            ),
            width=10
        )
    else:
        header = dbc.Col(
            dbc.Select(
                id={"type": "additional-step-type",
                    "index": str(index)},
                options=[
                    {"label": format_option(key), "value": key}
                    for key in methods
                ],
                value=method,
                placeholder="Step type",
                style={'width': '100%'}
            ),
            width=10
        )
    new_card = dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                header,
                dbc.Col(
                    html.Button(
                        html.I(className="fas fa-times",
                               style={'color': 'red'}),
                        className="ml-auto close",
                        id={"type": "step-close-button", "index": str(index)},
                        style={
                            'border': 'none',
                            'background': 'transparent',
                            'padding': '5px'
                        }
                    ),
                    width=2
                )
            ]),
        ]),
        dbc.CardBody([
            dbc.Row([
                html.Div(core_body, id={"type": "additional-step-core",
                                        "index": str(index)})
            ]),
        ]),
    ], id={"type": "additional-step-card", "index": str(index)})

    return new_card


# get the index of the dict containing the key-value
# in a list of dicts
def get_idx_dict_list(dict_list, key, value):
    idx = next((i for i, item in enumerate(dict_list)
                if item.__contains__(key) and item[key] == value), None)

    return idx


def parse_default_options(default_settings):
    """parse the default options from the definitions"""
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
    return def_opts


def parse_preprocessing_options(cards, steps, steps_args, fs_emg):
    """parse the preprocessing options from the cards and steps"""
    sel_opts = {}
    for n, card in enumerate(cards):
        card_id = int(card['index'])
        sel_opts[card_id] = {}
        sel_opts[card_id]['method'] = steps[n]
        sel_opts[card_id]['args_val'] = {}
        for item in steps_args[n]:
            arg_id = item['props']['children'][1]['props']['id']['type']
            if arg_id.startswith('processing-step-'):
                arg_name = item['props']['children'][1]['props']['name']
                arg_value = item['props']['children'][1]['props']['value']
                sel_opts[card_id]['args_val'][arg_name] = arg_value
        default_settings = definitions.get_defaults(
            sel_opts[card_id]['method'], fs_emg)
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
    return sel_opts


def apply_processing_pipeline(emg_ts, pipeline, suffix=''):
    """apply the processing pipeline to the EMG TimeSeries"""
    methods_div = {
        'filter': definitions.filter_methods,
        'ecg_removal': definitions.ecg_removal_methods,
        'envelope': definitions.envelope_methods,
        'baseline': definitions.baseline_methods}
    sig_order = ['raw', f'filt{suffix}', f'clean{suffix}', f'env{suffix}',
                 f'baseline{suffix}']
    _src_sig = 'raw'

    ecg_rem_counter = 0
    for _, options in pipeline.items():
        _src_idx = sig_order.index(_src_sig)
        method = options['method']
        _out_sig = next((sig for sig, methods in {
            'filt' + suffix: methods_div['filter'],
            'clean' + suffix: methods_div['ecg_removal'],
            'env' + suffix: methods_div['envelope'],
            'baseline' + suffix: methods_div['baseline']
        }.items() if method in methods), _src_sig)
        signal_io = (_src_sig, _out_sig if _out_sig in sig_order[_src_idx:]
                     else _src_sig)
        options['args_val']['signal_io'] = signal_io
        if method in methods_div['ecg_removal']:
            ecg_peakset_name = 'ecg_' + str(ecg_rem_counter)
            emg_ts.run('get_ecg_peaks', name=ecg_peakset_name,
                       overwrite=True)
            options['args_val']['ecg_peakset_name'] = ecg_peakset_name
            ecg_rem_counter += 1
        emg_ts.run(method, **options['args_val'])
        _src_sig = signal_io[1]
    return emg_ts


def pipeline_file_to_json(pipeline_file):
    _, content_string = pipeline_file.split(',')
    decoded = base64.b64decode(content_string).decode('utf8')
    return json.loads(decoded)


def parse_uploaded_pipeline(pipeline_file):
    card_counter_local = 0
    card_list = []
    data = pipeline_file_to_json(pipeline_file)
    pipeline = data[1]
    for i, options in pipeline.items():
        method = options['method']
        new_step_layout = get_processing_step_layout(
            int(i), method, fs=2048,
            values=options['args_val']
        )

        new_step_body = get_new_step_body(
            int(i), default=False, method=method, core_body=new_step_layout)
        card_list.append(new_step_body)
        card_list.append(html.P())

        card_counter_local += 1

    return card_list, card_counter_local


def check_default_cut_fs(default_fs: int, sampling_rate: int) -> int:
    """
    check compatibility of the base filter upper cut fs if the sampling fs
    is lower than twice the default value we need to adjust it
    """

    high_cut = default_fs

    if sampling_rate is None:
        return default_fs

    if default_fs > sampling_rate/2:
        # -1 because the butter filter fails if the cut-off fs
        # is equal to half the sampling rate

        high_cut = int(sampling_rate / 2) - 1

    return high_cut
