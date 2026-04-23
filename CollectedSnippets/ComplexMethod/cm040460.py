def associative_scan(f, elems, reverse=False, axis=0):
    # Ref: jax.lax.associative_scan
    if not callable(f):
        raise TypeError(f"`f` should be a callable. Received: f={f}")
    elems_flat = tree.flatten(elems)
    elems_flat = [convert_to_tensor(elem) for elem in elems_flat]

    def _flip(x, axis):
        x_ov = get_ov_output(x)
        ndim = len(x_ov.get_partial_shape())
        begin = [0] * ndim
        end = [0] * ndim
        strides = [1] * ndim
        strides[axis] = -1
        mask = [1] * ndim
        result = ov_opset.strided_slice(
            data=x_ov,
            begin=begin,
            end=end,
            strides=strides,
            begin_mask=mask,
            end_mask=mask,
        ).output(0)
        return OpenVINOKerasTensor(result)

    def _concat(tensors, axis):
        elems = [get_ov_output(t) for t in tensors]
        keras_types = [ov_to_keras_type(e.get_element_type()) for e in elems]
        if keras_types:
            target = OPENVINO_DTYPES[result_type(*keras_types)]
            elems = [
                ov_opset.convert(e, target).output(0)
                if e.get_element_type() != target
                else e
                for e in elems
            ]
        return OpenVINOKerasTensor(ov_opset.concat(elems, axis).output(0))

    def _unsqueeze(x, axis):
        x_ov = get_ov_output(x)
        const_axis = ov_opset.constant(axis, Type.i32).output(0)
        return OpenVINOKerasTensor(
            ov_opset.unsqueeze(x_ov, const_axis).output(0)
        )

    if reverse:
        elems_flat = [_flip(elem, axis) for elem in elems_flat]

    def _combine(a_flat, b_flat):
        a = tree.pack_sequence_as(elems, a_flat)
        b = tree.pack_sequence_as(elems, b_flat)
        c = f(a, b)
        return tree.flatten(c)

    num_elems = int(elems_flat[0].shape[axis])
    if not all(int(elem.shape[axis]) == num_elems for elem in elems_flat[1:]):
        raise ValueError(
            "Array inputs to associative_scan must have the same "
            "first dimension. (saw: {})".format(
                [elem.shape for elem in elems_flat]
            )
        )

    def _interleave(a, b, axis):
        n_a = a.shape[axis]
        n_b = b.shape[axis]

        a_common = slice_along_axis(a, 0, n_b, axis=axis)
        a_exp = _unsqueeze(a_common, axis + 1)
        b_exp = _unsqueeze(b, axis + 1)
        interleaved = _concat([a_exp, b_exp], axis + 1)

        interleaved_ov = get_ov_output(interleaved)
        orig_shape = ov_opset.shape_of(interleaved_ov, Type.i32).output(0)
        ndim = len(interleaved_ov.get_partial_shape())
        pre = ov_opset.slice(
            orig_shape,
            ov_opset.constant([0], Type.i32),
            ov_opset.constant([axis], Type.i32),
            ov_opset.constant([1], Type.i32),
        ).output(0)
        merged_dim = ov_opset.constant([n_b * 2], Type.i32).output(0)
        post = ov_opset.slice(
            orig_shape,
            ov_opset.constant([axis + 2], Type.i32),
            ov_opset.constant([ndim], Type.i32),
            ov_opset.constant([1], Type.i32),
        ).output(0)
        target_shape = ov_opset.concat([pre, merged_dim, post], 0).output(0)
        interleaved = OpenVINOKerasTensor(
            ov_opset.reshape(interleaved_ov, target_shape, False).output(0)
        )

        if n_a > n_b:
            last = slice_along_axis(a, n_b, n_b + 1, axis=axis)
            interleaved = _concat([interleaved, last], axis)

        return interleaved

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

    scanned_elems = _scan(elems_flat)
    if reverse:
        scanned_elems = [_flip(elem, axis) for elem in scanned_elems]
    return tree.pack_sequence_as(elems, scanned_elems)