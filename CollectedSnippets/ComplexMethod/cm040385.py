def scan(f, init, xs=None, length=None, reverse=False, unroll=1):
    # We have reimplemented `scan` to match the behavior of `jax.lax.scan`
    # Ref: tf.scan, jax.lax.scan
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
        # xs_flat = flatten_input(xs)
        xs_flat = tree.flatten(xs)
        xs_flat = [tf.convert_to_tensor(elem) for elem in xs_flat]
        n = int(length) if length is not None else tf.shape(xs_flat[0])[0]

    # TensorArrays are always flat
    xs_array = [
        tf.TensorArray(
            dtype=x.dtype,
            size=n,
            dynamic_size=False,
            element_shape=x.shape[1:],
            infer_shape=True,
        )
        for x in xs_flat
    ]
    xs_array = [x_a.unstack(x) for x_a, x in zip(xs_array, xs_flat)]

    init_flat = tree.flatten(init)
    carry_flat = [tf.convert_to_tensor(init) for init in init_flat]

    # Store the intermediate values
    # Note: there is a constraint that the output of `f` must have the same
    # shape and dtype as carry (`init`).
    ys_array = [
        tf.TensorArray(
            dtype=carry.dtype,
            size=n,
            dynamic_size=False,
            element_shape=carry.shape,
            infer_shape=True,
        )
        for carry in carry_flat
    ]
    carry_array = [
        tf.TensorArray(
            dtype=carry.dtype,
            size=1,
            dynamic_size=False,
            clear_after_read=False,
            element_shape=carry.shape,
            infer_shape=True,
        )
        for carry in carry_flat
    ]
    carry_array = [
        carry.write(0, c) for (carry, c) in zip(carry_array, carry_flat)
    ]

    def loop_body(i, carry_array, ys_array):
        packed_xs = (
            pack_input([xs.read(i) for xs in xs_array])
            if len(xs_array) > 0
            else None
        )
        packed_carry = pack_output([carry.read(0) for carry in carry_array])

        carry, ys = f(packed_carry, packed_xs)

        if ys is not None:
            flat_ys = tree.flatten(ys)
            ys_array = [ys.write(i, v) for (ys, v) in zip(ys_array, flat_ys)]
        if carry is not None:
            flat_carry = tree.flatten(carry)
            carry_array = [
                carry.write(0, v) for (carry, v) in zip(carry_array, flat_carry)
            ]
        next_i = i + 1 if not reverse else i - 1
        return (next_i, carry_array, ys_array)

    if isinstance(unroll, bool):
        unroll = max(n, 1) if unroll else 1

    _, carry_array, ys_array = tf.while_loop(
        lambda i, _1, _2: i >= 0 if reverse else i < n,
        loop_body,
        (n - 1 if reverse else 0, carry_array, ys_array),
        parallel_iterations=unroll,
    )

    ys_flat = [ys.stack() for ys in ys_array]
    carry_flat = [carry.read(0) for carry in carry_array]
    if xs is not None:
        n_static = xs_flat[0].get_shape().with_rank_at_least(1)[0]
        if not isinstance(n_static, int):
            for x in xs_flat[1:]:
                n_static.assert_is_compatible_with(
                    x.get_shape().with_rank_at_least(1)[0]
                )
        for r in ys_flat:
            r.set_shape(tf.TensorShape(n_static).concatenate(r.get_shape()[1:]))
    return pack_output(carry_flat), pack_output(ys_flat)