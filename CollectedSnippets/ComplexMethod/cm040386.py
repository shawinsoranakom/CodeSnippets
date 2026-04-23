def associative_scan(f, elems, reverse=False, axis=0):
    # Implementation is the same as tfp.math.scan_associative
    # with additional checks to ensure similar behavior with jax
    if not callable(f):
        raise TypeError(f"`f` should be a callable. Received: f={f}")
    elems_flat = tree.flatten(elems)
    elems_flat = [tf.convert_to_tensor(elem) for elem in elems_flat]
    if reverse:
        elems_flat = [tf.reverse(elem, [axis]) for elem in elems_flat]

    def _combine(a_flat, b_flat):
        a = tree.pack_sequence_as(elems, a_flat)
        b = tree.pack_sequence_as(elems, b_flat)
        c = f(a, b)
        c_flat = tree.flatten(c)
        return c_flat

    def _get_dim(x):
        return shape(x)[axis]

    # TODO add constant dim check
    num_elems = _get_dim(elems_flat[0])
    if not all(_get_dim(elem) == num_elems for elem in elems_flat[1:]):
        raise ValueError(
            "Array inputs to associative_scan must have the same "
            "first dimension. (saw: {})".format(
                [tf.shape(elem) for elem in elems_flat]
            )
        )

    def _interleave(a, b, axis):
        # [a b c ...] [d e f ...] -> [a d b e c f ...]
        num_elems_a = (
            a.shape[axis] if a.shape[axis] is not None else tf.shape(a)[axis]
        )
        num_elems_b = (
            b.shape[axis] if b.shape[axis] is not None else tf.shape(b)[axis]
        )

        # Note that interleaving implies rank(a)==rank(b).
        axis = tf.where(axis >= 0, axis, tf.rank(a) + axis)
        axis = (
            int(axis)  # Avoid ndarray values.
            if tf.get_static_value(axis) is not None
            else axis
        )

        def _interleave_with_b(a):
            a_shape = a.shape.as_list() if a.shape.rank is not None else None
            if isinstance(axis, int):
                b_shape_at_axis = b.shape[axis]
                num_elems_b_static = tf.get_static_value(
                    b_shape_at_axis
                    if b_shape_at_axis is not None
                    else tf.shape(b)[axis]
                )
            else:
                num_elems_b_static = None

            if (
                isinstance(axis, int)
                and a_shape is not None
                and num_elems_b_static is not None
                and all(
                    d is not None for i, d in enumerate(a_shape) if i != axis
                )
            ):
                new_shape = (
                    a_shape[:axis]
                    + [2 * num_elems_b_static]
                    + a_shape[axis + 1 :]
                )
            else:
                new_shape = tf.concat(
                    [
                        tf.shape(a)[:axis],
                        [2 * num_elems_b],
                        tf.shape(a)[axis + 1 :],
                    ],
                    axis=0,
                )
            return tf.reshape(
                # Work around lack of support for Tensor axes in
                # `tf.stack` by using `concat` and `expand_dims` instead.
                tf.concat(
                    [
                        tf.expand_dims(a, axis=axis + 1),
                        tf.expand_dims(b, axis=axis + 1),
                    ],
                    axis=axis + 1,
                ),
                new_shape,
            )

        return tf.cond(
            tf.equal(num_elems_a, num_elems_b + 1),
            lambda: tf.concat(
                [
                    _interleave_with_b(
                        tf.gather(
                            a,
                            tf.range(0, num_elems_a - 1),
                            axis=axis,
                        )
                    ),
                    tf.gather(
                        a,
                        tf.range(num_elems_a - 1, num_elems_a),
                        axis=axis,
                    ),
                ],
                axis=axis,
            ),
            lambda: _interleave_with_b(a),
        )

    # Dynamic-shape helper: resolve negative slice indices against the
    # actual (runtime) axis length using tf.shape, so that slicing works
    # inside tf.cond branches where the axis dim is statically unknown.
    def _dynamic_slice(x, start=0, stop=None, step=1):
        axis_len = tf.shape(x)[axis]
        if start is None:
            start = 0
        elif start < 0:
            start = start + axis_len
        if stop is None:
            stop = axis_len
        elif stop < 0:
            stop = stop + axis_len
        return tf.gather(x, tf.range(start, stop, delta=step), axis=axis)

    def _process_recursive_result(
        odd_elems, elems_level, is_even_length, use_dynamic_slicing=False
    ):
        """
        Helper function to process the result of a recursive _scan call.

        Takes the recursively scanned odd-indexed elements and applies the
        post-processing logic (combining, concatenation, and interleaving)
        that is common to both static and symbolic execution paths.

        Args:
            odd_elems: Result from _scan(reduced_elems)
            elems_level: Elements at the current level
            is_even_length: Boolean or symbolic tensor
                indicating if elem_length % 2 == 0
            use_dynamic_slicing: If True, uses _dynamic_slice for
                negative indices instead of slice_along_axis.
                Required when shapes are unknown at trace time.

        Returns:
            The final scanned result after interleaving even and odd
            elements.
        """
        _sl = (
            _dynamic_slice
            if use_dynamic_slicing
            else (
                lambda x, start=0, stop=None, step=1: slice_along_axis(
                    x, start, stop, step, axis=axis
                )
            )
        )

        def _get_even_results():
            return _combine(
                [_sl(odd_elem, 0, -1) for odd_elem in odd_elems],
                [_sl(elem, 2, None, 2) for elem in elems_level],
            )

        def _get_odd_results():
            return _combine(
                [odd_elem for odd_elem in odd_elems],
                [_sl(elem, 2, None, 2) for elem in elems_level],
            )

        # For Python-level conditionals (static), is_even_length is a bool
        # For symbolic conditionals, is_even_length is a Tensor,
        # handled via tf.cond
        if isinstance(is_even_length, bool):
            results = (
                _get_even_results() if is_even_length else _get_odd_results()
            )
        else:
            results = tf.cond(
                is_even_length, _get_even_results, _get_odd_results
            )

        even_elems = [
            tf.concat([_sl(elem, 0, 1), result], axis=axis)
            for (elem, result) in zip(elems_level, results)
        ]
        return list(
            builtins.map(
                lambda a, b: _interleave(a, b, axis=axis),
                even_elems,
                odd_elems,
            )
        )

    # Max recursion depth for dynamic-shape fallback. Supports sequences upto
    # 2^48 elements.
    _max_num_levels = 48

    def _scan(elems):
        elem_length = _get_dim(elems[0])

        # Try to get the static value of elem_length to avoid infinite
        # recursion in tf.function when elem_length is symbolic.
        static_elem_length = tf.get_static_value(elem_length)

        # Early return before doing any slicing work.
        if static_elem_length is not None and int(static_elem_length) < 2:
            return elems

        a = [slice_along_axis(elem, 0, -1, step=2, axis=axis) for elem in elems]
        b = [
            slice_along_axis(elem, 1, None, step=2, axis=axis) for elem in elems
        ]
        reduced_elems = _combine(a, b)

        def _handle_base_case_elem_length_two():
            return [
                tf.concat(
                    [slice_along_axis(elem, 0, 1, axis=axis), reduced_elem],
                    axis=axis,
                )
                for (reduced_elem, elem) in zip(reduced_elems, elems)
            ]

        def _handle_base_case_elem_length_three():
            reduced_reduced_elems = _combine(
                reduced_elems,
                [slice_along_axis(elem, 2, 3, axis=axis) for elem in elems],
            )
            return [
                tf.concat(
                    [
                        slice_along_axis(elem, 0, 1, axis=axis),
                        reduced_elem,
                        reduced_reduced_elem,
                    ],
                    axis=axis,
                )
                for (reduced_reduced_elem, reduced_elem, elem) in zip(
                    reduced_reduced_elems, reduced_elems, elems
                )
            ]

        # If we have a static value, use Python conditionals to avoid
        # tracing the recursive case unnecessarily
        if static_elem_length is not None:
            static_elem_length = int(static_elem_length)
            if static_elem_length == 2:
                return _handle_base_case_elem_length_two()
            elif static_elem_length == 3:
                return _handle_base_case_elem_length_three()
            else:
                # Recursive case with static length
                odd_elems = _scan(reduced_elems)
                # Use Python bool for static length
                is_even = static_elem_length % 2 == 0
                return _process_recursive_result(odd_elems, elems, is_even)

        # Fallback for symbolic lengths: use TF-cond recursion (following
        # the TFP scan_associative pattern) with a level counter to bound
        # the Python-level recursion depth. At each level tf.cond chooses
        # between the base case and the recursive case at runtime.
        return tf.cond(
            tf.less(elem_length, 2),
            lambda: elems,
            lambda: _scan_dynamic(_max_num_levels, elems),
        )

    def _scan_dynamic(level, elems):
        """Recursive associative scan for symbolic (dynamic) lengths.

        Uses a level counter to bound the Python-level unrolling depth,
        mirroring the approach from tfp.math.scan_associative.  Each
        level is guarded by tf.cond so only the needed depth executes.
        """
        elem_length = tf.shape(elems[0])[axis]

        a = [_dynamic_slice(elem, 0, -1, step=2) for elem in elems]
        b = [_dynamic_slice(elem, 1, None, step=2) for elem in elems]
        reduced_elems = _combine(a, b)

        def _handle_base_case_two():
            return [
                tf.concat([_dynamic_slice(elem, 0, 1), reduced_elem], axis=axis)
                for (reduced_elem, elem) in zip(reduced_elems, elems)
            ]

        def _handle_base_case_three():
            reduced_reduced_elems = _combine(
                reduced_elems,
                [_dynamic_slice(elem, 2, 3) for elem in elems],
            )
            return [
                tf.concat(
                    [
                        _dynamic_slice(elem, 0, 1),
                        reduced_elem,
                        reduced_reduced_elem,
                    ],
                    axis=axis,
                )
                for (reduced_reduced_elem, reduced_elem, elem) in zip(
                    reduced_reduced_elems, reduced_elems, elems
                )
            ]

        at_base_case = tf.logical_or(
            tf.equal(elem_length, 2), tf.equal(elem_length, 3)
        )
        base_value = lambda: tf.cond(
            tf.equal(elem_length, 2),
            _handle_base_case_two,
            _handle_base_case_three,
        )

        if level <= 0:
            return base_value()

        def _recursive_case():
            odd_elems = _scan_dynamic(level - 1, reduced_elems)
            is_even = tf.equal(elem_length % 2, 0)
            return _process_recursive_result(
                odd_elems, elems, is_even, use_dynamic_slicing=True
            )

        return tf.cond(at_base_case, base_value, _recursive_case)

    scans = _scan(elems_flat)
    if reverse:
        scans = [tf.reverse(scanned, [axis]) for scanned in scans]

    return tree.pack_sequence_as(elems, scans)