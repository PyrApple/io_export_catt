def freq_to_str(freq):
    """convert float freqency to string"""

    # kHz
    if( freq < 1000.0 ):
        return '{0}Hz'.format(int(freq))

    # Hz
    return '{0}kHz'.format(int(freq/1000.0))