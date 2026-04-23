def compute_output_spec(self, x):
        if not isinstance(x, (tuple, list)) or len(x) != 2:
            raise ValueError(
                "Input `x` should be a tuple of two tensors - real and "
                f"imaginary. Received: x={x}"
            )
        real, imag = x
        # Both real and imaginary parts should have the same shape.
        if real.shape != imag.shape:
            raise ValueError(
                "Input `x` should be a tuple of two tensors - real and "
                "imaginary. Both the real and imaginary parts should have the "
                f"same shape. Received: x[0].shape = {real.shape}, "
                f"x[1].shape = {imag.shape}"
            )
        if len(real.shape) < 2:
            raise ValueError(
                f"Input should have rank >= 2. "
                f"Received: input.shape = {real.shape}"
            )
        if real.shape[-2] is not None:
            output_size = (
                real.shape[-2] - 1
            ) * self.sequence_stride + self.fft_length
            if self.length is not None:
                output_size = self.length
            elif self.center:
                output_size = output_size - (self.fft_length // 2) * 2
        else:
            output_size = None
            if self.length is not None:
                output_size = self.length
        new_shape = real.shape[:-2] + (output_size,)
        return KerasTensor(shape=new_shape, dtype=real.dtype)