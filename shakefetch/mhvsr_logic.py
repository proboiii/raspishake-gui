import hvsrpy
import numpy as np

def process_mhvsr(file_paths, preprocessing_settings, processing_settings):
    """
    Processes MHVSR data from a list of files.
    """
    srecords = hvsrpy.read(file_paths)
    srecords = hvsrpy.preprocess(srecords, preprocessing_settings)
    hvsr = hvsrpy.process(srecords, processing_settings)
    return hvsr

def get_default_preprocessing_settings(window_length=150):
    """
    Returns default preprocessing settings for HVSR analysis.
    """
    settings = hvsrpy.settings.HvsrPreProcessingSettings()
    settings.detrend = "linear"
    settings.window_length_in_seconds = window_length
    settings.orient_to_degrees_from_north = 0.0
    settings.filter_corner_frequencies_in_hz = (None, None)
    settings.ignore_dissimilar_time_step_warning = False
    return settings

def get_default_processing_settings(bandwidth=40, combine_method='geometric_mean'):
    """
    Returns default processing settings for HVSR analysis.
    """
    settings = hvsrpy.settings.HvsrTraditionalProcessingSettings()
    settings.window_type_and_width = ("tukey", 0.2)
    settings.smoothing = dict(operator="konno_and_ohmachi",
                               bandwidth=bandwidth,
                               center_frequencies_in_hz=np.geomspace(0.2, 50, 200))
    settings.method_to_combine_horizontals = combine_method
    settings.handle_dissimilar_time_steps_by = "frequency_domain_resampling"
    return settings