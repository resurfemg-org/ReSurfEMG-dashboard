from enum import Enum
import inspect
from app import variables
import numpy as np
from resurfemg.data_connector.data_classes import TimeSeries

FILE_IDENTIFIER = 'resurfemg_paramfile'


class ProcessTypology(Enum):
    CUT = '0'
    BAND_PASS = '1'
    HIGH_PASS = '2'
    LOW_PASS = '3'
    ECG_REMOVAL = '4'
    ENVELOPE = '5'


class EcgRemovalMethods(Enum):
    ICA = '1'
    GATING = '2'
    NONE = '3'


class EnvelopeMethod(Enum):
    RMS = '1'
    FILTERING = '2'
    NONE = '3'


class GatingMethod(Enum):
    ZERO_FILL = '0'
    INTERPOLATE = '1'
    AVERAGE_PRIOR_SEGMENT = '2'
    RUNNING_AVERAGE_RMS = '3'


class BreathSelectionMethod(Enum):
    VARIABILITY = '1'
    SHANNON_ENTROPY = '2'
    SAMPLE_ENTROPY = '3'
    LOG_REMAPPING = '4'


# default values for preprocessing
sampling_freq = variables.get_emg_freq()
default_bandpass_low = 3
default_bandpass_high = 450
default_first_cut_percentage = 3
default_first_cut_tolerance = 5
default_envelope_cut_fs = 150
default_ecg_removal_value = EcgRemovalMethods.GATING
default_envelope_value = EnvelopeMethod.FILTERING

# default values for features extraction
default_breath_method = BreathSelectionMethod.VARIABILITY


class ComputedFeatures:
    BREATHS_COUNT = 'BREATHS COUNT'
    MAX_AMPLITUDE = 'MAX AMPLITUDE'
    BASELINE_AMPLITUDE = 'BASELINE AMPLITUDE'
    TONIC_AMPLITUDE = 'TONIC AMPLITUDE'
    AUC = 'AUC'
    RISE_TIME = 'RISE TIME [ms]'
    ACTIVITY_DURATION = 'ACTIVITY DURATION [ms]'
    PEAK_POSITION = 'PEAK POSITION [%]'

    # list of computed features
    features_list = [BREATHS_COUNT,
                     MAX_AMPLITUDE,
                     AUC,
                     RISE_TIME,
                     ACTIVITY_DURATION,
                     PEAK_POSITION]


# IDs for graphical elements

# DATA UPLOAD PAGE
CONFIRM_CENTERED = 'confirm-centered'
CWD = 'cwd'
CWD_FILES = 'cwd-files'
EMG_FILE_UPDATED = 'emg-file-updated'
EMG_fs_DIV = 'emg-fs-div'
EMG_OPEN_CENTERED = 'open-centered-emg'
EMG_SAMPLING_fs = 'emg-fs'
FILE_PATH_INPUT = 'file-path-input'
LISTED_FILES = 'listed_file'
MODAL_CENTERED = 'modal-centered'
PARENT_DIR = 'parent-dir'
PATH_BTN = 'path-button'
PATH_SELECT = 'path-select'
VENT_FILE_UPDATED = 'ventilator-file-updated'
VENT_fs_DIV = 'ventilator-fs-div'
VENT_OPEN_CENTERED = 'open-centered-vent'
VENT_SAMPLING_fs = 'ventilator-fs'
PATH_ERROR = 'path-error'
DIR_FAVORITES = 'dir-favorite'
INVALID_DIR = 'invalid-dir'

# FEATURES PAGE
EMG_FILENAME_FEATURES = 'emg-filename-features'
LOAD_FEATURES_DIV = 'load-features-div'
FEATURES_COMPUTE_BTN = 'features-compute-btn'
FEATURES_COMPUTE_TOOLTIP = 'features-compute-tooltip'
FEATURES_DOWNLOAD_BTN = 'features-download-btn'
FEATURES_DOWNLOAD_DCC = 'features-download-dcc'
FEATURES_DOWNLOAD_TOOLTIP = 'features-download-tooltip'
FEATURES_EMG_GRAPH = 'features-emg-graph'
FEATURES_EMG_GRAPH_DIV = 'features-emg-graph-div'
FEATURES_LOADING = 'features-loading'
FEATURES_SELECT_LEAD = 'features-select-lead'
FEATURES_SELECT_COMPUTATION = 'features-select-computation'
FEATURES_TABLE = 'features-table'

f_list = inspect.getmembers(TimeSeries, predicate=inspect.isfunction)
f_names = [name for name, _ in f_list if not name.startswith("_")]
f_names = [name for name in f_names if not name.startswith("plot")]

# f_filt = ['filter_emg']
# f_ecg = ['get_ecg_peaks', 'gating', 'wavelet_denoising']
# f_post = ['envelope', 'baseline']
# f_feat = ['calculate_time_products', 'detect_emg_breaths']
# f_tests = [name for name in f_names if name.startswith("test")]
def get_defaults(method=None, fs=2048):
    override_defaults = {
        'filter_emg': {
            'arg_defaults': {
                'hp_cf': 20.0,
                'lp_cf': 500.0,
                'order': 3},
            'arg_options': {
                'hp_cf': (0.1, fs/2-1, 0.1),
                'lp_cf': (1, fs/2-1, 0.1),
                'order': (1, 10, 1)},
            'set_args': {},
            'omit_args': [],
            },
        'gating': {
            'arg_defaults':{
                'gate_width_samples': fs//10,
                'fill_method': 3},
            'arg_options':{
                'gate_width_samples': (1, fs, 1),
                'fill_method': {0:'Zeros', 1:'Raw interpolate',
                                2:'Prior average', 3:'RMS interpolate'}},
            'set_args':{
                'ecg_peakset_name': 'ecg',
                },
            'omit_args': [],
            },
        'wavelet_denoising': {
            'arg_defaults':{
                'n': int(np.log(fs/20) // np.log(2)),
                'fixed_threshold': 4.5},
            'arg_options':{
                'n': (1, None, 1),
                'fixed_threshold': (0.5, None, 0.1)},
            'set_args':{
                'ecg_peakset_name': 'ecg'},
            'omit_args': [],
            },
        'envelope': {
            'arg_defaults': {
                'env_window': int(0.1*fs),
                'env_type': 'rms'},
            'arg_options': {
                'env_window': (1, None, 1),
                'env_type': {'RMS': 'rms', 'ARV':'arv'}},
            'set_args': {},
            'omit_args': ['ci_alpha']
            },
        'baseline': {
            'arg_defaults': {
                'percentile': 33,
                'window_s': int(7.5*fs),
                'step_s': fs // 5},
            'arg_options': {
                'percentile': (0, 100, 1),
                'window_s': (1, None, 1),
                'step_s': (1, None, 1),
            },
            'set_args': {
                'base_method': 'default',
            },
            'omit_args': [
                'perc_window',
                'augm_percentile',
                'parameter_name',
                'ma_window'],
            },
    }
    if method is None:
        return override_defaults
    return override_defaults.get(method, None)

def get_default_pipeline(fs_emg=2048):
    # default pipeline for EMG processing
    default_pipeline = {
        'filter_emg': get_defaults('filter_emg', fs=fs_emg),
        'gating': get_defaults('gating', fs=fs_emg),
        'envelope': get_defaults('envelope', fs=fs_emg),
        'baseline': get_defaults('baseline', fs=fs_emg),
    }
    return default_pipeline

# Function: envelope
#   Args and Defaults: {'env_window': None, 'env_type': None, 'ci_alpha': None}
# Function: baseline
#   Args and Defaults: {'percentile': 33, 'window_s': None, 'step_s': None, 'method': 'default', 'augm_percentile': 25, 'ma_window': None, 'perc_window': None}

# Function: detect_emg_breaths
#   Args and Defaults: {'threshold': 0, 'prominence_factor': 0.5, 'min_peak_width_s': None, 'peak_set_name': 'breaths', 'start_idx': 0, 'end_idx': None, 'overwrite': False}
# Function: calculate_time_products
#   Args and Defaults: {'peak_set_name': None, 'include_aub': True, 'aub_window_s': None, 'aub_reference_signal': None, 'parameter_name': None}

# Function: link_peak_set
#   Args and Defaults: {'peak_set_name': None, 't_reference_peaks': None, 'linked_peak_set_name': None}

# Function: set_peaks
#   Args and Defaults: {'peak_idxs': None, 'signal': None, 'peak_set_name': None, 'overwrite': False}
# Function: signal_type_data
#   Args and Defaults: {}

# Function: test_emg_quality
#   Args and Defaults: {'peak_set_name': None, 'cutoff': None, 'skip_tests': None, 'parameter_names': None, 'verbose': True}
# Function: test_linked_peak_sets
#   Args and Defaults: {'peak_set_name': None, 'linked_timeseries': None, 'linked_peak_set_name': None, 'parameter_names': None, 'cutoff': None, 'skip_tests': None, 'verbose': True}
# Function: test_pocc_quality
#   Args and Defaults: {'peak_set_name': None, 'cutoff': None, 'skip_tests': None, 'parameter_names': None, 'verbose': True}

processing_methods = {}
for name, func in f_list:
    if name in f_names:
        args = func.__code__.co_varnames[:func.__code__.co_argcount]
        defaults = func.__defaults__ or ()
        non_def_args = len(args) - len(defaults)
        arg_defaults = {arg: defaults[i - non_def_args] if i >= non_def_args
                        else None for i, arg in enumerate(args)}
        arg_defaults.pop('self', None)
        arg_defaults.pop('signal_type', None)
        arg_defaults.pop('kwargs', None)
        processing_methods[name] = arg_defaults

input_types = {
    int: 'number',
    float: 'number',
    str: 'text',
    bool: 'checkbox',
}

ecg_removal_methods = [
    'gating',
    'wavelet_denoising',
]
