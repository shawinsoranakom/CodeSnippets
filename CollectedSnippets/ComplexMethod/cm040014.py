def __init__(
        self,
        mode="log",
        frame_length=256,
        frame_step=None,
        fft_length=None,
        window="hann",
        periodic=False,
        scaling="density",
        padding="valid",
        expand_dims=False,
        data_format=None,
        **kwargs,
    ):
        if frame_step is not None and (
            frame_step > frame_length or frame_step < 1
        ):
            raise ValueError(
                "`frame_step` should be a positive integer not greater than "
                f"`frame_length`. Received frame_step={frame_step}, "
                f"frame_length={frame_length}"
            )

        if fft_length is not None and fft_length < frame_length:
            raise ValueError(
                "`fft_length` should be not less than `frame_length`. "
                f"Received fft_length={fft_length}, frame_length={frame_length}"
            )

        if fft_length is not None and (fft_length & -fft_length) != fft_length:
            warnings.warn(
                "`fft_length` is recommended to be a power of two. "
                f"Received fft_length={fft_length}"
            )

        all_modes = ["log", "magnitude", "psd", "real", "imag", "angle", "stft"]

        if mode not in all_modes:
            raise ValueError(
                "Output mode is invalid, it must be one of "
                f"{', '.join(all_modes)}. Received: mode={mode}"
            )

        if scaling is not None and scaling not in ["density", "spectrum"]:
            raise ValueError(
                "Scaling is invalid, it must be `None`, 'density' "
                f"or 'spectrum'. Received scaling={scaling}"
            )

        if padding not in ["valid", "same"]:
            raise ValueError(
                "Padding is invalid, it should be 'valid', 'same'. "
                f"Received: padding={padding}"
            )

        if isinstance(window, str):
            # throws an exception for invalid window function
            scipy.signal.get_window(window, 1)

        super().__init__(**kwargs)

        self.mode = mode

        self.frame_length = frame_length
        self.frame_step = frame_step
        self._frame_step = frame_step or self.frame_length // 2
        self.fft_length = fft_length
        self._fft_length = fft_length or (
            2 ** int(math.ceil(math.log2(frame_length)))
        )

        self.window = window
        self.periodic = periodic
        self.scaling = scaling
        self.padding = padding
        self.expand_dims = expand_dims
        self.data_format = backend.standardize_data_format(data_format)
        self.input_spec = layers.input_spec.InputSpec(ndim=3)