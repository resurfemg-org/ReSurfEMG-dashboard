"""
Copyright 2023 Netherlands eScience Center and University of Twente
Licensed under the Apache License, version 2.0. See LICENSE for details.

This file contains functions to work functions from the ReSurfEMG library.
"""

from typing import List

from dash import Input, Output, callback, dcc, ctx, State, html, ALL, callback_context
from app import app, variables
from resurfemg.postprocessing import features as feat
from resurfemg import helper_functions as hf
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import utils
from pathlib import Path
from dash.exceptions import PreventUpdate
from definitions import ComputedFeatures, BreathSelectionMethod, FEATURES_COMPUTE_BTN, FEATURES_DOWNLOAD_BTN, FEATURES_DOWNLOAD_DCC
from definitions import (EMG_FILENAME_FEATURES, FEATURES_EMG_GRAPH, FEATURES_EMG_GRAPH_DIV,
                         FEATURES_SELECT_LEAD, LOAD_FEATURES_DIV, FEATURES_TABLE, FEATURES_SELECT_COMPUTATION)

features_df = None


class Breath:

    def __init__(self,
                 start_sample: int = None,
                 stop_sample: int = None,
                 peak_sample: int = None,
                 amplitude: np.array = None,
                 baseline: np.array = None):
        self.start_sample = start_sample
        self.stop_sample = stop_sample
        self.amplitude = amplitude
        self.baseline = baseline
        self.peak_sample = peak_sample


# on loading add the PAGE
@callback(Output(EMG_FILENAME_FEATURES, 'children'),
          Input(LOAD_FEATURES_DIV, 'data'))
def show_filename(data):
    """
    When loading the page, the path of the file selected is displayed in th EMG_FILENAME_FEATURES
    """
    filename = variables.get_emg_filename()

    return filename if filename is not None else []


@callback(Output(FEATURES_SELECT_LEAD, 'options'),
          Input(LOAD_FEATURES_DIV, 'data'))
def show_filename(data):
    """
    When loading the page, the dropdown menu for selecting the lead is populated
    """
    data = variables.get_emg_processed()

    if data is not None:
        options = [{'label': 'Lead ' + str(n), 'value': n} for n in range(data.shape[0])]
        return options
    return []


@callback(Output(FEATURES_EMG_GRAPH_DIV, 'children'),
          Input(FEATURES_SELECT_LEAD, 'value'))
def show_graph(value):
    """
    When loading the page, the path of the file selected is displayed in th EMG_FILENAME_FEATURES
    """
    data = variables.get_emg_processed()

    if data is not None and value is not None:
        lead = data[int(value)]
        time_array = utils.get_time_array(lead.shape[0], variables.get_emg_freq())

        graph = get_slider_graph(lead, time_array)
        return graph

    return []


@callback(Output(FEATURES_TABLE, 'data'),
          State(FEATURES_EMG_GRAPH, 'relayoutData'),
          State(FEATURES_SELECT_COMPUTATION, 'value'),
          State(FEATURES_SELECT_LEAD, 'value'),
          State(FEATURES_EMG_GRAPH, 'figure'),
          Input(FEATURES_SELECT_COMPUTATION, 'value'),
          Input(FEATURES_COMPUTE_BTN, 'n_clicks'),
          prevent_initial_call=True)
def show_graph(slidebar_stat, method_stat, lead_n, figure, method_input, btn_input):
    """
    When the slide bar is updated by the user, or the computation method is changed
    computes the features and updates the table
    """

    global features_df

    data = variables.get_emg_processed()
    fs = variables.get_emg_freq()
    time_array = utils.get_time_array(data[int(lead_n)].shape[0], fs)

    if slidebar_stat is not None and 'xaxis.range' in slidebar_stat:
        start_sample = (np.abs(time_array - slidebar_stat['xaxis.range'][0])).argmin()
        stop_sample = (np.abs(time_array - slidebar_stat['xaxis.range'][1])).argmin()
    elif slidebar_stat is not None and ('xaxis.range[0]' and 'xaxis.range[1]' in slidebar_stat):
        start_sample = (np.abs(time_array - slidebar_stat['xaxis.range[0]'])).argmin()
        stop_sample = (np.abs(time_array - slidebar_stat['xaxis.range[1]'])).argmin()
    else:
        start_sample = 0
        stop_sample = time_array.shape[0]

    breaths = get_breaths(int(lead_n), start_sample, stop_sample, method_stat)

    features_df = create_features_dataframe(breaths, fs)

    features = [{ComputedFeatures.BREATHS_COUNT: len(breaths),
                 ComputedFeatures.MAX_AMPLITUDE: str(np.round(features_df['maxima'].to_numpy().flatten().mean(), 2)) + ' ± ' + str(
                     np.round(features_df['maxima'].to_numpy().flatten().std(), 2)),
                 ComputedFeatures.AUC: str(np.round(features_df['auc'].to_numpy().flatten().mean(), 2)) + ' ± ' + str(
                     np.round(features_df['auc'].to_numpy().flatten().std(), 2)),
                 ComputedFeatures.RISE_TIME: str(np.round(features_df['rise_time'].to_numpy().flatten().mean(), 2)) + ' ± ' + str(
                     np.round(features_df['rise_time'].to_numpy().flatten().std(), 2)),
                 ComputedFeatures.ACTIVITY_DURATION: str(np.round(features_df['length'].to_numpy().flatten().mean(), 2)) + ' ± ' + str(
                     np.round(features_df['length'].to_numpy().flatten().std(), 2)),
                 ComputedFeatures.PEAK_POSITION: str(np.round(features_df['peak_position'].to_numpy().flatten().mean(), 2)) + ' ± ' + str(
                     np.round(features_df['peak_position'].to_numpy().flatten().std(), 2))}]

    return features


# download the csv file with the features
@callback(Output(FEATURES_DOWNLOAD_DCC, 'data'),
          Input(FEATURES_DOWNLOAD_BTN, 'n_clicks'),
          prevent_initial_call=True)
def download_data(click):
    global features_df

    if features_df is not None:
        features_file = dcc.send_data_frame(features_df.to_csv, 'features.csv')
        return features_file


def get_slider_graph(emg: np.array, time: np.array):
    """
    Produces a line plot with a range slider selector of the signal specified in the emg argument, with the
    time basis specified in the time argument.
        Args:
            emg: a numpy array containing a single lead of the emg signal to plot
            time: a numpy array containing the time basis for the emg signal

    """

    traces = [{
        'x': time,
        'y': emg,
        'type': 'scatter',
        'mode': 'lines',
        'name': 'a_level'
    }]

    figure = go.Figure(
        data=traces,
        layout=go.Layout(
            xaxis={
                'rangeslider': {'visible': True}
            },
        )
    )
    figure.update_layout(
        title='EMG lead',
        xaxis_title='Time [s]',
        yaxis_title='micro Volts',
    )

    graph = [
        dcc.Graph(
            id=FEATURES_EMG_GRAPH,
            figure=figure
        )
    ]

    return graph


def get_features_table(emg: np.array, start_sample: int, stop_sample: int):
    """
    Produces a table with the features computed over the selected signal.
        Args:
            emg: a numpy array containing a single lead of the emg signal to plot
            start_sample: number of the sample where the signal to be computed starts
            stop_sample: number of the sample where the signal to be computed stops

    """

    return []


def get_breaths(n_channel: int, start_sample: int, stop_sample: int, method: str) -> List[Breath]:
    """
    Produces a list of breaths from the time window in the signal.
        Args:
            emg: a numpy array containing a single lead of the emg signal to analyse
            start_sample: number of the sample where the signal to be computed starts
            stop_sample: number of the sample where the signal to be computed stops
            method: the method used to compute the breaths

    """
    emg_timeseries = variables.get_emg_timeseries()
    emg = emg_timeseries[n_channel].y_env
    
    # TODO: Introduce different methods for breath detection
    emg_timeseries[n_channel].baseline()
    emg_timeseries[n_channel].detect_emg_breaths()
    emg_timeseries[n_channel].peaks['breaths'].detect_on_offset(
        baseline=emg_timeseries[n_channel].y_baseline
    )
    baseline = emg_timeseries[n_channel].y_baseline
    emg_timeseries[n_channel].calculate_time_products(
        peak_set_name='breaths') 
    emg_timeseries[n_channel].test_emg_quality(peak_set_name='breaths')
    emg_timeseries[n_channel].peaks['breaths'].sanitize()
    peak_df = emg_timeseries[n_channel].peaks['breaths'].peak_df

    breaths = [Breath(start_sample=int(row['start_idx']),
                      stop_sample=int(row['end_idx']-row['start_idx']),
                      peak_sample=int(row['peak_idx']-row['start_idx']),
                      amplitude=emg[int(row['start_idx']):int(row['end_idx'])],
                      baseline=baseline[
                          int(row['start_idx']):int(row['end_idx'])])
               for _, row in peak_df.iterrows()]
    

    # if method == BreathSelectionMethod.LOG_REMAPPING.value:
    #     index_hold = []
    #     for slice in slice_iterator(big_list, slice_length):
    #         entropy_index = hf.entropical(slice)
    #         index_hold.append(entropy_index)

    #     high_decision_cutoff = 0.9 * ((np.max(index_hold)) - (np.min(index_hold))) + np.min(index_hold)
    #     decision_cutoff = 0.5 * ((np.max(index_hold)) - (np.min(index_hold))) + np.min(index_hold)

    #     rms_rolled = hf.vect_naive_rolling_rms(index_hold, 100)  # so rms is rms entropy

    # elif method == BreathSelectionMethod.VARIABILITY.value:
    #     variability = hf.variability_maker(big_list, segment_size=slice_length, method='variance', fill_method='avg')
    #     high_decision_cutoff = 0.5 * ((np.max(variability)) - (np.min(variability))) + np.min(variability)
    #     decision_cutoff = 0.05 * ((np.max(variability)) - (np.min(variability))) + np.min(variability)
        
    #     rms_rolled = hf.vect_naive_rolling_rms(variability, 100)  # so rms is rms variability

    # elif method == BreathSelectionMethod.SHANNON_ENTROPY.value:
    #     index_hold = []
    #     for slice in slice_iterator(big_list, slice_length):
    #         entropy_index = hf.entropy_maker(slice, method='scipy')
    #         index_hold.append(entropy_index)

    #     high_decision_cutoff = 0.9 * ((np.max(index_hold)) - (np.min(index_hold))) + np.min(index_hold)
    #     decision_cutoff = 0.5 * ((np.max(index_hold)) - (np.min(index_hold))) + np.min(index_hold)

    #     rms_rolled = hf.vect_naive_rolling_rms(index_hold, 100)  # so rms is rms entropy

    # elif method == BreathSelectionMethod.SAMPLE_ENTROPY.value:

    #     # N.B. the window length is an empirical tradeoff between speed and quality of the results.
    #     # It is not what is recommended in the literature
    #     slice_length = 300
    #     tolerance = 0.3 * np.std(big_list)
    #     index_hold = []
    #     for slice in slice_iterator(big_list, slice_length):
    #         entropy_index = hf.sampen_optimized(slice, tolerance=tolerance)
    #         index_hold.append(entropy_index)

    #     # N.B. the cutoffs have still to be evaluated!
    #     high_decision_cutoff = 0.5 * ((np.max(index_hold)) - (np.min(index_hold))) + np.min(index_hold)
    #     decision_cutoff = 0.5 * ((np.max(index_hold)) - (np.min(index_hold))) + np.min(index_hold)

    #     rms_rolled = hf.vect_naive_rolling_rms(index_hold, 100)  # so rms is rms entropy

    # hi = np.array(hf.zero_one_for_jumps_base(rms_rolled, high_decision_cutoff))
    # lo = np.array(hf.zero_one_for_jumps_base(rms_rolled, decision_cutoff))

    # rhi = hf.ranges_of(hi)
    # rlo = hf.ranges_of(lo)

    # keep = hf.intersections(rlo, rhi)

    # seven_line = np.zeros(len(rms_rolled))
    # for seven_range in keep:
    #     seven_line[seven_range.to_slice()] = 7

    # breaths = [Breath(start_sample=int(keep[i].start+start_sample),
    #                 stop_sample=int(keep[i + 1].start+start_sample),
    #                 amplitude=emg[int(keep[i].start+start_sample):int(keep[i + 1].start+start_sample)])
    #         for i, element in enumerate(keep[:-1])]

    return breaths


def get_breaths_length(breaths: List[Breath]) -> List[int]:
    """
    Computes and returns the numpy array containing the length of each breath
    of the breaths list
        Args:
            breaths: list of the breaths

    """
    length = [(breath.stop_sample - breath.start_sample) for breath in breaths]

    return length


def get_breaths_maxima(breaths: List[Breath]) -> List[int]:
    """
    Computes and returns the numpy array containing the maximum
    of each breath of the breaths list
        Args:
            breaths: list of the breaths

    """
    maxima = [feat.amplitude(
                breath.amplitude, [breath.peak_sample], breath.baseline)
              for breath in breaths]

    return maxima


def get_breaths_auc(breaths: List[Breath]) -> List[float]:
    """
    Computes and returns the numpy array containing the area under the curve
    of each breath of the breaths list
        Args:
            breaths: list of the breaths

    """
    sampling_rate = variables.get_emg_freq()
    auc = [feat.time_product(
        breath.amplitude,
        fs=sampling_rate,
        start_idxs=[0],
        end_idxs=[len(breath.amplitude) - 1],
    )
        for breath in breaths]

    return auc


def get_breaths_rise_time(breaths: List[Breath], sampling_fs: int) -> List[float]:
    """
    Computes and returns the numpy array containing the rise time in milliseconds
    of each breath of the breaths list
        Args:
            breaths: list of the breaths
            sampling_fs: sampling fs of the EMG
    """
    samples_to_milliseconds = sampling_fs/1000
    rise_times = [
        feat.time_to_peak(
            breath.amplitude,
            [0],
            [(len(breath.amplitude) - 1)])[0]/samples_to_milliseconds
        for breath in breaths

    ]

    return rise_times


def get_breaths_peak_position(breaths: List[Breath]) -> List[float]:
    """
    Computes and returns the numpy array containing the rise time
    of each breath of the breaths list
        Args:
            breaths: list of the breaths
    """
    rise_times = [
        feat.time_to_peak(
            breath.amplitude,
            [0],
            [(len(breath.amplitude) - 1)])[1]*100
        for breath in breaths

    ]

    return rise_times


def create_features_dataframe(breaths: List[Breath], sampling_fs: int) -> pd.DataFrame:
    """
    creates the pandas dataframe containing all the computed features
        Args:
            breaths: list of the breaths
            sampling_fs: sampling fs of the EMG
    """
    start_samples = []
    stop_samples = []
    for breath in breaths:
        start_samples.append(breath.start_sample)
        stop_samples.append(breath.stop_sample)

    length = get_breaths_length(breaths)
    maxima = get_breaths_maxima(breaths)
    auc = get_breaths_auc(breaths)
    rise_times = get_breaths_rise_time(breaths, sampling_fs=sampling_fs)
    peak_position = get_breaths_peak_position(breaths)

    d = {'start_samples': start_samples,
         'stop_samples': stop_samples,
         'length': length,
         'maxima': maxima,
         'auc': auc,
         'rise_time': rise_times,
         'peak_position': peak_position}

    df = pd.DataFrame(d)

    df.index.name = 'breath_number'

    return df


def slice_iterator(lst, sliceLen):
    for i in range(len(lst) - sliceLen + 1):
        yield lst[i:i + sliceLen]
