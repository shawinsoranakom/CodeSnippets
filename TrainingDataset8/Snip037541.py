def marshall_audio(
    coordinates: str,
    proto: AudioProto,
    data: MediaData,
    mimetype: str = "audio/wav",
    start_time: int = 0,
    sample_rate: Optional[int] = None,
) -> None:
    """Marshalls an audio proto, using data and url processors as needed.

    Parameters
    ----------
    coordinates : str
    proto : The proto to fill. Must have a string field called "url".
    data : str, bytes, BytesIO, numpy.ndarray, or file opened with
            io.open()
        Raw audio data or a string with a URL pointing to the file to load.
        If passing the raw data, this must include headers and any other bytes
        required in the actual file.
    mimetype : str
        The mime type for the audio file. Defaults to "audio/wav".
        See https://tools.ietf.org/html/rfc4281 for more info.
    start_time : int
        The time from which this element should start playing. (default: 0)
    sample_rate: int or None
        Optional param to provide sample_rate in case of numpy array
    """

    proto.start_time = start_time

    if isinstance(data, str) and url(data):
        proto.url = data

    else:
        data = _maybe_convert_to_wav_bytes(data, sample_rate)
        _marshall_av_media(coordinates, proto, data, mimetype)