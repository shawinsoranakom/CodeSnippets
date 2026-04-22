def audio(
        self,
        data: MediaData,
        format: str = "audio/wav",
        start_time: int = 0,
        *,
        sample_rate: Optional[int] = None,
    ) -> "DeltaGenerator":
        """Display an audio player.

        Parameters
        ----------
        data : str, bytes, BytesIO, numpy.ndarray, or file opened with
                io.open().
            Raw audio data, filename, or a URL pointing to the file to load.
            Raw data formats must include all necessary file headers to match the file
            format specified via ``format``.
            If ``data`` is a numpy array, it must either be a 1D array of the waveform
            or a 2D array of shape ``(num_channels, num_samples)`` with waveforms
            for all channels. See the default channel order at
            http://msdn.microsoft.com/en-us/library/windows/hardware/dn653308(v=vs.85).aspx
        format : str
            The mime type for the audio file. Defaults to 'audio/wav'.
            See https://tools.ietf.org/html/rfc4281 for more info.
        start_time: int
            The time from which this element should start playing.
        sample_rate: int or None
            The sample rate of the audio data in samples per second. Only required if
            ``data`` is a numpy array.

        Example
        -------
        >>> import streamlit as st
        >>> import numpy as np
        >>> audio_file = open('myaudio.ogg', 'rb')
        >>> audio_bytes = audio_file.read()
        >>>
        >>> st.audio(audio_bytes, format='audio/ogg')
        >>>
        >>> sample_rate = 44100  # 44100 samples per second
        >>> seconds = 2  # Note duration of 2 seconds
        >>> frequency_la = 440  # Our played note will be 440 Hz
        >>> # Generate array with seconds*sample_rate steps, ranging between 0 and seconds
        >>> t = np.linspace(0, seconds, seconds * sample_rate, False)
        >>> # Generate a 440 Hz sine wave
        >>> note_la = np.sin(frequency_la * t * 2 * np.pi)
        >>>
        >>> st.audio(note_la, sample_rate=sample_rate)

        .. output::
           https://doc-audio.streamlitapp.com/
           height: 865px

        """
        audio_proto = AudioProto()
        coordinates = self.dg._get_delta_path_str()

        is_data_numpy_array = type_util.is_type(data, "numpy.ndarray")

        if is_data_numpy_array and sample_rate is None:
            raise StreamlitAPIException(
                "`sample_rate` must be specified when `data` is a numpy array."
            )
        if not is_data_numpy_array and sample_rate is not None:
            st.warning(
                "Warning: `sample_rate` will be ignored since data is not a numpy "
                "array."
            )

        marshall_audio(coordinates, audio_proto, data, format, start_time, sample_rate)
        return self.dg._enqueue("audio", audio_proto)