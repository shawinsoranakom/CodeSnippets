def compute_output_spec(self, x):
        if len(x.shape) != 4:
            raise ValueError(
                "`depth_to_space` requires a 4D input tensor. "
                f"Received: x.shape={x.shape}"
            )
        if self.data_format == "channels_last":
            b, h, w, c = x.shape
        else:
            b, c, h, w = x.shape

        if c is not None and c % (self.block_size**2) != 0:
            raise ValueError(
                f"The number of channels ({c}) must be divisible by "
                f"block_size**2 ({self.block_size**2})."
            )

        new_c = c // (self.block_size**2) if c is not None else None
        new_h = h * self.block_size if h is not None else None
        new_w = w * self.block_size if w is not None else None

        if self.data_format == "channels_last":
            output_shape = (b, new_h, new_w, new_c)
        else:
            output_shape = (b, new_c, new_h, new_w)

        return KerasTensor(output_shape, dtype=x.dtype)