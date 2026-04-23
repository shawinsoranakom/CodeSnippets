def _maybe_convert_to_wav_bytes(
    data: MediaData, sample_rate: Optional[int]
) -> MediaData:
    """Convert data to wav bytes if the data type is numpy array."""
    if type_util.is_type(data, "numpy.ndarray") and sample_rate is not None:
        data = _make_wav(cast("npt.NDArray[Any]", data), sample_rate)
    return data