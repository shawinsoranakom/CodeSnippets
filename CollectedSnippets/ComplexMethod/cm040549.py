def compute_output_spec(self, xs):
        dtypes_to_resolve = []
        out_shapes = []
        for x in xs:
            shape = list(x.shape)
            if len(shape) == 0:
                shape = [1, 1, 1]
            elif len(shape) == 1:
                shape = [1, shape[0], 1]
            elif len(shape) == 2:
                shape = shape + [1]
            out_shapes.append(shape)
            dtypes_to_resolve.append(getattr(x, "dtype", type(x)))

        first_shape = out_shapes[0]
        total_depth = 0
        for shape in out_shapes:
            if not shape_equal(shape, first_shape, axis=[2], allow_none=True):
                raise ValueError(
                    "Every value in `xs` must have the same shape except on "
                    f"the `axis` dim. But found element of shape {shape}, "
                    f"which is different from the first element's "
                    f"shape {first_shape}."
                )
            if total_depth is None or shape[2] is None:
                total_depth = None
            else:
                total_depth += shape[2]

        output_shape = list(first_shape)
        output_shape[2] = total_depth
        dtype = dtypes.result_type(*dtypes_to_resolve)
        return KerasTensor(output_shape, dtype=dtype)