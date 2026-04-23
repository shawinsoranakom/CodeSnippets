def __call__(self, shape, dtype=None):
        """Returns a tensor object initialized as specified by the initializer.

        The shape is assumed to be `(T, 1, F // 2 + 1)`, where `T` is the size
        of the given window, and `F` is the number of frequency bands. Only half
        the frequency bands are used, which is a common practice in STFT,
        because the second half are the conjugates of the first half in
        a reversed order.

        Args:
            shape: Shape of the tensor.
            dtype: Optional dtype of the tensor. Only numeric or boolean dtypes
                are supported. If not specified, `keras.backend.floatx()`
                is used, which default to `float32` unless you configured it
                otherwise (via `keras.backend.set_floatx(float_dtype)`).
        """
        dtype = standardize_dtype(dtype)
        frame_length, input_channels, fft_length = shape

        win = None
        scaling = 1
        if self.window is not None:
            win = self.window
            if isinstance(win, str):
                # Using SciPy since it provides more windowing functions,
                # easier to be compatible with multiple backends.
                win = scipy.signal.get_window(win, frame_length, self.periodic)
            win = ops.convert_to_tensor(win, dtype=dtype)
            if len(win.shape) != 1 or win.shape[-1] != frame_length:
                raise ValueError(
                    "The shape of `window` must be equal to [frame_length]."
                    f"Received: window shape={win.shape}"
                )
            win = ops.reshape(win, [frame_length, 1, 1])
            if self.scaling == "density":
                scaling = ops.sqrt(ops.sum(ops.square(win)))
            elif self.scaling == "spectrum":
                scaling = ops.sum(ops.abs(win))

        _fft_length = (fft_length - 1) * 2
        freq = ops.divide(
            ops.reshape(
                ops.arange(fft_length, dtype=dtype), (1, 1, fft_length)
            ),
            _fft_length,
        )
        time = ops.reshape(
            ops.arange(frame_length, dtype=dtype), (frame_length, 1, 1)
        )
        args = ops.multiply(ops.multiply(-2, time), freq) * ops.arccos(
            ops.cast(-1, dtype)
        )

        if self.side == "real":
            kernel = ops.cast(ops.cos(args), dtype)
        else:
            kernel = ops.cast(ops.sin(args), dtype)

        if win is not None:
            kernel = ops.divide(ops.multiply(kernel, win), scaling)
        return kernel