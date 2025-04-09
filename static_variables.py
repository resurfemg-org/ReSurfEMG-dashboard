from threading import Lock


_singleton = None
_lock = Lock()


def get_singleton():
    with _lock:
        global _singleton

        if _singleton is None:
            _singleton = Variables()

        return _singleton


class Variables:

    def __init__(self):
        self.emg_filename = None
        self.ventilator_filename = None
        self.emg = None
        self.emg_freq = None
        self.emg_timeseries = None
        self.ventilator = None
        self.ventilator_freq = None
        self.vent_timeseries = None
        self.emg_processed = None
        self.emg_processed_default = None

    def set_emg_filename(self, emg_filename):
        self.emg_filename = emg_filename

    def get_emg_filename(self):
        return self.emg_filename

    def set_ventilator_filename(self, ventilator_filename):
        self.ventilator_filename = ventilator_filename

    def get_ventilator_filename(self):
        return self.ventilator_filename

    def set_emg(self, emg):
        self.emg = emg

    def get_emg(self):
        return self.emg

    def set_emg_timeseries(self, emg_timeseries):
        self.emg_timeseries = emg_timeseries

    def get_emg_timeseries(self):
        return self.emg_timeseries

    def set_ventilator(self, ventilator):
        self.ventilator = ventilator

    def get_ventilator(self):
        return self.ventilator

    def set_vent_timeseries(self, vent_timeseries):
        self.vent_timeseries = vent_timeseries

    def get_vent_timeseries(self):
        return self.emg_timeseries

    def set_emg_freq(self, emg_freq):
        self.emg_freq = emg_freq

    def get_emg_freq(self):
        return self.emg_freq

    def set_ventilator_freq(self, ventilator_freq):
        self.ventilator_freq = ventilator_freq

    def get_ventilator_freq(self):
        return self.ventilator_freq

    def set_emg_processed(self, emg_processed):
        self.emg_processed = emg_processed

    def get_emg_processed(self):
        return self.emg_processed

    def set_emg_processed_default(self, emg_processed_default):
        self.emg_processed_default = emg_processed_default

    def get_emg_processed_default(self):
        return self.emg_processed_default
