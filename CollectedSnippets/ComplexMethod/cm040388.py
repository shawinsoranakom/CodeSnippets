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