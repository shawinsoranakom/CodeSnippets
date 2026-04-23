def _interleave(a, b, axis):
        """Given two Tensors of static shape, interleave them along axis."""
        if not (
            a.shape[axis] == b.shape[axis] or a.shape[axis] == b.shape[axis] + 1
        ):
            raise ValueError(
                "Shapes are incompatible for associative_scan interleaving. "
                f"a.shape[{axis}]={a.shape[axis]}, "
                f"b.shape[{axis}]={b.shape[axis]}"
            )

        # we want to get a: [a1, a2], b: [b1, b2]
        # to a: [a1, 0, a2, 0], b: [0, b1, 0, b2]
        a_shape = list(a.shape)
        a_shape[axis] = a.shape[axis] * 2 - 1

        b_shape = list(b.shape)
        b_shape[axis] = b.shape[axis] * 2 - 1

        a_dil = np.zeros(a_shape)
        np.copyto(slice_along_axis(a_dil, 0, None, 2, axis), a)
        b_dil = np.zeros(b_shape)
        np.copyto(slice_along_axis(b_dil, 0, None, 2, axis), b)

        a_pad = [[0, 0] for _ in range(a.ndim)]
        a_pad[axis][-1] = 1 if a.shape[axis] == b.shape[axis] else 0

        b_pad = [[0, 0] for _ in range(b.ndim)]
        b_pad[axis] = [1, 0] if a.shape[axis] == b.shape[axis] else [1, 1]

        op = np.bitwise_or if a.dtype == np.bool_ else np.add
        return op(
            np.pad(a_dil, a_pad),
            np.pad(b_dil, b_pad),
        )