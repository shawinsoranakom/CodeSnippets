def associative_scan(f, elems, reverse=False, axis=0):
    # Ref: jax.lax.associative_scan
    if not callable(f):
        raise TypeError(f"`f` should be a callable. Received: f={f}")
    elems_flat = tree.flatten(elems)
    elems_flat = [convert_to_tensor(elem) for elem in elems_flat]
    if reverse:
        elems_flat = [np.flip(elem, (axis,)) for elem in elems_flat]

    def _combine(a_flat, b_flat):
        a = tree.pack_sequence_as(elems, a_flat)
        b = tree.pack_sequence_as(elems, b_flat)
        c = f(a, b)
        c_flat = tree.flatten(c)
        return c_flat

    num_elems = int(elems_flat[0].shape[axis])
    if not all(int(elem.shape[axis]) == num_elems for elem in elems_flat[1:]):
        raise ValueError(
            "Array inputs to associative_scan must have the same "
            "first dimension. (saw: {})".format(
                [elem.shape for elem in elems_flat]
            )
        )

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

    def _scan(elems):
        num_elems = elems[0].shape[axis]
        if num_elems < 2:
            return elems

        reduced_elems = _combine(
            [
                slice_along_axis(elem, 0, -1, step=2, axis=axis)
                for elem in elems
            ],
            [
                slice_along_axis(elem, 1, None, step=2, axis=axis)
                for elem in elems
            ],
        )

        odd_elems = _scan(reduced_elems)
        if num_elems % 2 == 0:
            even_elems = _combine(
                [slice_along_axis(e, 0, -1, axis=axis) for e in odd_elems],
                [
                    slice_along_axis(e, 2, None, step=2, axis=axis)
                    for e in elems
                ],
            )
        else:
            even_elems = _combine(
                odd_elems,
                [
                    slice_along_axis(e, 2, None, step=2, axis=axis)
                    for e in elems
                ],
            )

        even_elems = [
            np.concatenate(
                [slice_along_axis(elem, 0, 1, axis=axis), result],
                axis=axis,
            )
            for (elem, result) in zip(elems, even_elems)
        ]
        return list(
            builtins.map(
                functools.partial(_interleave, axis=axis), even_elems, odd_elems
            )
        )

    scans = _scan(elems_flat)
    if reverse:
        scans = [np.flip(scanned, (axis,)) for scanned in scans]

    return tree.pack_sequence_as(elems, scans)