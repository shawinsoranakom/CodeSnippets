def call(self, inputs):
        dtype = inputs.dtype
        if backend.standardize_dtype(dtype) not in {
            "float16",
            "float32",
            "float64",
        }:
            raise TypeError(
                "Invalid input type. Expected `float16`, `float32` or "
                f"`float64`. Received: input type={dtype}"
            )

        real_signal = None
        imag_signal = None
        power = None

        if self.mode != "imag":
            real_signal = self._apply_conv(inputs, self.real_kernel)
        if self.mode != "real":
            imag_signal = self._apply_conv(inputs, self.imag_kernel)

        if self.mode == "real":
            return self._adjust_shapes(real_signal)
        elif self.mode == "imag":
            return self._adjust_shapes(imag_signal)
        elif self.mode == "angle":
            return self._adjust_shapes(ops.arctan2(imag_signal, real_signal))
        elif self.mode == "stft":
            return self._adjust_shapes(
                ops.concatenate([real_signal, imag_signal], axis=2)
            )
        else:
            power = ops.square(real_signal) + ops.square(imag_signal)

        if self.mode == "psd":
            return self._adjust_shapes(
                power
                + ops.pad(
                    power[:, :, 1:-1, :], [[0, 0], [0, 0], [1, 1], [0, 0]]
                )
            )
        linear_stft = self._adjust_shapes(
            ops.sqrt(ops.maximum(power, backend.epsilon()))
        )

        if self.mode == "magnitude":
            return linear_stft
        else:
            return ops.log(ops.maximum(linear_stft, backend.epsilon()))