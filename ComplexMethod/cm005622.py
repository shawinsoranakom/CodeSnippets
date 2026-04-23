def ffmpeg_microphone(
    sampling_rate: int,
    chunk_length_s: float,
    format_for_conversion: str = "f32le",
    ffmpeg_input_device: str | None = None,
    ffmpeg_additional_args: list[str] | None = None,
):
    """
    Helper function to read audio from a microphone using ffmpeg. The default input device will be used unless another
    input device is specified using the `ffmpeg_input_device` argument. Uses 'alsa' on Linux, 'avfoundation' on MacOS and
    'dshow' on Windows.

    Arguments:
        sampling_rate (`int`):
            The sampling_rate to use when reading the data from the microphone. Try using the model's sampling_rate to
            avoid resampling later.
        chunk_length_s (`float` or `int`):
            The length of the maximum chunk of audio to be sent returned.
        format_for_conversion (`str`, defaults to `f32le`):
            The name of the format of the audio samples to be returned by ffmpeg. The standard is `f32le`, `s16le`
            could also be used.
        ffmpeg_input_device (`str`, *optional*):
            The identifier of the input device to be used by ffmpeg (i.e. ffmpeg's '-i' argument). If unset,
            the default input device will be used. See `https://www.ffmpeg.org/ffmpeg-devices.html#Input-Devices`
            for how to specify and list input devices.
        ffmpeg_additional_args (`list[str]`, *optional*):
            Additional arguments to pass to ffmpeg, can include arguments like -nostdin for running as a background
            process. For example, to pass -nostdin to the ffmpeg process, pass in ["-nostdin"]. If passing in flags
            with multiple arguments, use the following convention (eg ["flag", "arg1", "arg2]).

    Returns:
        A generator yielding audio chunks of `chunk_length_s` seconds as `bytes` objects of length
        `int(round(sampling_rate * chunk_length_s)) * size_of_sample`.
    """
    ar = f"{sampling_rate}"
    ac = "1"
    if format_for_conversion == "s16le":
        size_of_sample = 2
    elif format_for_conversion == "f32le":
        size_of_sample = 4
    else:
        raise ValueError(f"Unhandled format `{format_for_conversion}`. Please use `s16le` or `f32le`")

    system = platform.system()

    if system == "Linux":
        format_ = "alsa"
        input_ = ffmpeg_input_device or "default"
    elif system == "Darwin":
        format_ = "avfoundation"
        input_ = ffmpeg_input_device or ":default"
    elif system == "Windows":
        format_ = "dshow"
        input_ = ffmpeg_input_device or _get_microphone_name()

    ffmpeg_additional_args = [] if ffmpeg_additional_args is None else ffmpeg_additional_args

    ffmpeg_command = [
        "ffmpeg",
        "-f",
        format_,
        "-i",
        input_,
        "-ac",
        ac,
        "-ar",
        ar,
        "-f",
        format_for_conversion,
        "-fflags",
        "nobuffer",
        "-hide_banner",
        "-loglevel",
        "quiet",
        "pipe:1",
    ]

    ffmpeg_command.extend(ffmpeg_additional_args)

    chunk_len = int(round(sampling_rate * chunk_length_s)) * size_of_sample
    iterator = _ffmpeg_stream(ffmpeg_command, chunk_len)
    yield from iterator