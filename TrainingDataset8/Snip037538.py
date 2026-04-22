def _validate_and_normalize(data: "npt.NDArray[Any]") -> Tuple[bytes, int]:
    """Validates and normalizes numpy array data.
    We validate numpy array shape (should be 1d or 2d)
    We normalize input data to int16 [-32768, 32767] range.

    Parameters
    ----------
    data : numpy array
        numpy array to be validated and normalized

    Returns
    -------
    Tuple of (bytes, int)
        (bytes, nchan)
        where
         - bytes : bytes of normalized numpy array converted to int16
         - nchan : number of channels for audio signal. 1 for mono, or 2 for stereo.
    """
    # we import numpy here locally to import it only when needed (when numpy array given
    # to st.audio data)
    import numpy as np

    data = np.array(data, dtype=float)

    if len(data.shape) == 1:
        nchan = 1
    elif len(data.shape) == 2:
        # In wave files,channels are interleaved. E.g.,
        # "L1R1L2R2..." for stereo. See
        # http://msdn.microsoft.com/en-us/library/windows/hardware/dn653308(v=vs.85).aspx
        # for channel ordering
        nchan = data.shape[0]
        data = data.T.ravel()
    else:
        raise StreamlitAPIException("Numpy array audio input must be a 1D or 2D array.")

    if data.size == 0:
        return data.astype(np.int16).tobytes(), nchan

    max_abs_value = np.max(np.abs(data))
    # 16-bit samples are stored as 2's-complement signed integers,
    # ranging from -32768 to 32767.
    # scaled_data is PCM 16 bit numpy array, that's why we multiply [-1, 1] float
    # values to 32_767 == 2 ** 15 - 1.
    np_array = (data / max_abs_value) * 32767
    scaled_data = np_array.astype(np.int16)
    return scaled_data.tobytes(), nchan