def _make_wav(data: "npt.NDArray[Any]", sample_rate: int) -> bytes:
    """
    Transform a numpy array to a PCM bytestring
    We use code from IPython display module to convert numpy array to wave bytes
    https://github.com/ipython/ipython/blob/1015c392f3d50cf4ff3e9f29beede8c1abfdcb2a/IPython/lib/display.py#L146
    """
    # we import wave here locally to import it only when needed (when numpy array given
    # to st.audio data)
    import wave

    scaled, nchan = _validate_and_normalize(data)

    with io.BytesIO() as fp, wave.open(fp, mode="wb") as waveobj:
        waveobj.setnchannels(nchan)
        waveobj.setframerate(sample_rate)
        waveobj.setsampwidth(2)
        waveobj.setcomptype("NONE", "NONE")
        waveobj.writeframes(scaled)
        return fp.getvalue()