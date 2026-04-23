def compute_output_shape(self, input_shape):
        if self.data_format == "channels_first":
            if (
                input_shape[2] is not None
                and sum(self.cropping[0]) >= input_shape[2]
            ) or (
                input_shape[3] is not None
                and sum(self.cropping[1]) >= input_shape[3]
            ):
                raise ValueError(
                    "Values in `cropping` argument should be smaller than the "
                    "corresponding spatial dimension of the input. Received: "
                    f"input_shape={input_shape}, cropping={self.cropping}"
                )
            return (
                input_shape[0],
                input_shape[1],
                (
                    input_shape[2] - self.cropping[0][0] - self.cropping[0][1]
                    if input_shape[2] is not None
                    else None
                ),
                (
                    input_shape[3] - self.cropping[1][0] - self.cropping[1][1]
                    if input_shape[3] is not None
                    else None
                ),
            )
        else:
            if (
                input_shape[1] is not None
                and sum(self.cropping[0]) >= input_shape[1]
            ) or (
                input_shape[2] is not None
                and sum(self.cropping[1]) >= input_shape[2]
            ):
                raise ValueError(
                    "Values in `cropping` argument should be smaller than the "
                    "corresponding spatial dimension of the input. Received: "
                    f"input_shape={input_shape}, cropping={self.cropping}"
                )
            return (
                input_shape[0],
                (
                    input_shape[1] - self.cropping[0][0] - self.cropping[0][1]
                    if input_shape[1] is not None
                    else None
                ),
                (
                    input_shape[2] - self.cropping[1][0] - self.cropping[1][1]
                    if input_shape[2] is not None
                    else None
                ),
                input_shape[3],
            )