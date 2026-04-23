def compute_output_spec(self, x1, x2):
        x1_shape = getattr(x1, "shape", [])
        x2_shape = getattr(x2, "shape", [])
        if len(x1_shape) != 1:
            raise ValueError(
                "`x1` must be a 1-dimensional tensor, but received"
                + f"shape {x1_shape}"
            )
        if len(x2_shape) != 1:
            raise ValueError(
                "`x2` must be a 1-dimensional tensor, but received"
                + f"shape {x2_shape}"
            )
        x1_len, x2_len = x1_shape[0], x2_shape[0]
        output_shape = (
            np.maximum(x1_len, x2_len) - np.minimum(x1_len, x2_len) + 1,
        )
        if self.mode == "same":
            output_shape = (np.maximum(x1_len, x2_len),)
        elif self.mode == "full":
            output_shape = (x1_len + x2_len - 1,)
        if self.mode not in ("valid", "same", "full"):
            raise ValueError(
                "`mode` must be either `valid`, `same`, or `full`, but"
                f"received: {self.mode}"
            )
        output_dtype = dtypes.result_type(
            getattr(x1, "dtype", type(x1)),
            getattr(x2, "dtype", type(x2)),
        )
        if output_dtype == "int64":
            output_dtype = "float64"
        elif output_dtype not in ["bfloat16", "float16", "float64"]:
            output_dtype = "float32"
        return KerasTensor(output_shape, dtype=output_dtype)