def _scan(elems):
        num_elems = elems[0].shape[axis]
        if num_elems < 2:
            return elems

        reduced_elems = _combine(
            [slice_along_axis(e, 0, -1, step=2, axis=axis) for e in elems],
            [slice_along_axis(e, 1, None, step=2, axis=axis) for e in elems],
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
            _concat(
                [slice_along_axis(elem, 0, 1, axis=axis), result],
                axis,
            )
            for elem, result in zip(elems, even_elems)
        ]
        return [_interleave(e, o, axis) for e, o in zip(even_elems, odd_elems)]