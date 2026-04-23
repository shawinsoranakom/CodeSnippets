def compute_output_spec(self, x):
        if len(x.shape) != 4:
            raise ValueError(
                "`space_to_depth` requires a 4D input tensor. "
                f"Received: x.shape={x.shape}"
            )
        if self.data_format == "channels_last":
            b, h, w, c = x.shape
        else:
            b, c, h, w = x.shape

        if h is not None and h % self.block_size != 0:
            raise ValueError(
                f"Height ({h}) must be divisible by block_size "
                f"({self.block_size})."
            )
        if w is not None and w % self.block_size != 0:
            raise ValueError(
                f"Width ({w}) must be divisible by block_size "
                f"({self.block_size})."
            )

        new_c = c * (self.block_size**2) if c is not None else None
        new_h = h // self.block_size if h is not None else None
        new_w = w // self.block_size if w is not None else None

        if self.data_format == "channels_last":
            output_shape = (b, new_h, new_w, new_c)
        else:
            output_shape = (b, new_c, new_h, new_w)

        return KerasTensor(output_shape, dtype=x.dtype)