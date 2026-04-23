def scan(f, init, xs=None, length=None, reverse=False, unroll=1):
    # Ref: jax.lax.scan
    if not callable(f):
        raise TypeError(f"`f` should be a callable. Received: f={f}")
    if not isinstance(unroll, bool):
        if not isinstance(unroll, int) or unroll < 1:
            raise ValueError(
                "`unroll` must be an positive integer or boolean. "
                f"Received: unroll={unroll}"
            )
    if xs is None and length is None:
        raise ValueError("Got no `xs` to scan over and `length` not provided.")

    input_is_sequence = tree.is_nested(xs)
    output_is_sequence = tree.is_nested(init)

    def pack_input(x):
        return tree.pack_sequence_as(xs, x) if input_is_sequence else x[0]

    def pack_output(x):
        return tree.pack_sequence_as(init, x) if output_is_sequence else x[0]

    if xs is None:
        xs_flat = []
        n = int(length)
    else:
        xs_flat = tree.flatten(xs)
        xs_flat = [convert_to_tensor(elem) for elem in xs_flat]
        n = (
            int(length)
            if length is not None
            else (shape(xs_flat[0])[0] if xs_flat else 0)
        )

    init_flat = tree.flatten(init)
    init_flat = [convert_to_tensor(i) for i in init_flat]
    init = pack_output(init_flat)

    dummy_y = []
    for i in init_flat:
        i_ov = get_ov_output(i)
        zero = ov_opset.constant(0, i_ov.get_element_type()).output(0)
        shape_node = ov_opset.shape_of(i_ov, Type.i32).output(0)
        dummy_y.append(
            OpenVINOKerasTensor(ov_opset.broadcast(zero, shape_node).output(0))
        )

    carry = init
    ys = []
    maybe_reversed = reversed if reverse else lambda x: x
    for i in maybe_reversed(range(n)):
        xs_slice = [x[i] for x in xs_flat]
        packed_xs = pack_input(xs_slice) if len(xs_slice) > 0 else None
        carry, y = f(carry, packed_xs)
        ys.append(y if y is not None else dummy_y)

    def _stack(tensors):
        elems = [get_ov_output(t) for t in tensors]
        const_axis = ov_opset.constant(0, Type.i32).output(0)
        elems = [ov_opset.unsqueeze(e, const_axis).output(0) for e in elems]
        return OpenVINOKerasTensor(ov_opset.concat(elems, 0).output(0))

    stacked_y = tree.map_structure(
        lambda *y: _stack(list(y)), *maybe_reversed(ys)
    )
    return carry, stacked_y