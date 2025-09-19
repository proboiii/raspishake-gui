from obspy.clients.earthworm import Client
from obspy import UTCDateTime

def fetch_waveforms(params):
    """
    Fetches seismic waveforms using an Earthworm client.
    """
    client = Client(params['host'], params['port'])
    stream = client.get_waveforms(
        params['net'],
        params['sta'],
        params['loc'],
        params['cha'],
        params['start_time'],
        params['end_time']
    )
    return stream
