def compute_output_spec(self, x):
        output_dtype = backend.standardize_dtype(x.dtype)
        if "int" in output_dtype or output_dtype == "bool":
            output_dtype = backend.floatx()
        if self.axis is None:
            axis = tuple(range(len(x.shape)))
        else:
            axis = self.axis
        num_axes = len(axis)
        if num_axes == 1 and isinstance(self.ord, str):
            raise ValueError(
                "Invalid `ord` argument for vector norm. "
                f"Received: ord={self.ord}"
            )
        elif num_axes == 2 and self.ord not in (
            None,
            "fro",
            "nuc",
            float("inf"),
            float("-inf"),
            1,
            -1,
            2,
            -2,
        ):
            raise ValueError(
                "Invalid `ord` argument for matrix norm. "
                f"Received: ord={self.ord}"
            )
        return KerasTensor(
            reduce_shape(x.shape, axis=self.axis, keepdims=self.keepdims),
            dtype=output_dtype,
        )