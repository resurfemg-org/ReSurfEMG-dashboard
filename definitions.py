from enum import Enum
from app import variables


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
