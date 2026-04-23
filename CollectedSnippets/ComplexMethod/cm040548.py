def compute_output_spec(self, x1, x2):
        x1_shape = list(getattr(x1, "shape", []))
        x2_shape = list(getattr(x2, "shape", []))
        dtype = dtypes.result_type(
            getattr(x1, "dtype", type(x1)),
            getattr(x2, "dtype", type(x2)),
        )
        if x1_shape == [] or x2_shape == []:
            return multiply(x1, x2)
        if len(x1_shape) == 1 and len(x2_shape) == 1:
            return KerasTensor([], dtype=dtype)
        if len(x2_shape) == 1:
            if x1_shape[-1] != x2_shape[0]:
                raise ValueError(
                    "Shape must match on the last axis of `x1` and `x2` when "
                    "`x1` is N-d array while `x2` is 1-D, but receive shape "
                    f"`x1.shape={x1.shape}` and x2.shape=`{x2.shape}`."
                )
            return KerasTensor(x1_shape[:-1], dtype=dtype)

        if (
            x1_shape[-1] is None
            or x2_shape[-2] is None
            or x1_shape[-1] == x2_shape[-2]
        ):
            del x1_shape[-1]
            del x2_shape[-2]
            return KerasTensor(x1_shape + x2_shape, dtype=dtype)

        raise ValueError(
            "Shape must match on the last axis of `x1` and second last "
            "axis of `x2` when `x1` is N-d array while `x2` is M-D, but "
            f"received `x1.shape={x1.shape}` and x2.shape=`{x2.shape}`."
        )