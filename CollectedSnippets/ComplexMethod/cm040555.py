def compute_output_spec(self, x1, x2):
        x1_shape = list(getattr(x1, "shape", []))
        x2_shape = list(getattr(x2, "shape", []))
        dtype = dtypes.result_type(
            getattr(x1, "dtype", type(x1)),
            getattr(x2, "dtype", type(x2)),
        )
        if not isinstance(self.axes, int):
            x1_select_shape = [x1_shape[ax] for ax in self.axes[0]]
            x2_select_shape = [x2_shape[ax] for ax in self.axes[1]]
            if not shape_equal(
                x1_select_shape, x2_select_shape, allow_none=True
            ):
                raise ValueError(
                    "Shape mismatch on `x1[axes[0]]` and `x2[axes[1]]`, "
                    f"received {x1_select_shape} and {x2_select_shape}."
                )

            for ax in self.axes[0]:
                x1_shape[ax] = -1
            for ax in self.axes[1]:
                x2_shape[ax] = -1

            x1_shape = list(filter((-1).__ne__, x1_shape))
            x2_shape = list(filter((-1).__ne__, x2_shape))

            output_shape = x1_shape + x2_shape
            return KerasTensor(output_shape, dtype=dtype)

        if self.axes <= 0:
            output_shape = x1_shape + x2_shape
        else:
            output_shape = x1_shape[: -self.axes] + x2_shape[self.axes :]

        return KerasTensor(output_shape, dtype=dtype)