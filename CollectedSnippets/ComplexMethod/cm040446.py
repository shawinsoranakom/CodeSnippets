def wrapped(*args):
        out = func(*args)
        if isinstance(out, (list, tuple)):
            out_shapes = [ops.shape(x) for x in out]
        else:
            out_shapes = [out.shape]

        if expected_output_core_dims is None:
            output_core_dims = [()] * len(out_shapes)
        else:
            output_core_dims = expected_output_core_dims
            if len(output_core_dims) > 1 and not isinstance(out, tuple):
                raise TypeError(
                    "output must be a tuple when multiple outputs "
                    f"are expected, got: {out}"
                )
            if len(out_shapes) != len(output_core_dims):
                raise TypeError(
                    "wrong number of output arguments: "
                    f"expected {len(output_core_dims)}, got {len(out_shapes)}"
                )

        sizes = dict(dim_sizes)
        for shape, core_dims in zip(out_shapes, output_core_dims):
            _vectorize_update_dim_sizes(sizes, shape, core_dims, is_input=False)

        return out