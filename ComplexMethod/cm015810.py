def argsort_sort_assert_equal(
        test_case_inst,
        x,
        y,
        *,
        atol=None,
        rtol=None,
        equal_nan=True,
        exact_dtype=True,
        exact_stride=False,
    ):
        if is_argsort:
            if not isinstance(x, torch.Tensor):
                raise AssertionError(f"Expected torch.Tensor, got {type(x)}")
            if not isinstance(y, torch.Tensor):
                raise AssertionError(f"Expected torch.Tensor, got {type(y)}")
        else:
            # The first tensor is the sorted values and can be asserted via
            # the usual means
            for t in (x, y):
                if not isinstance(t, tuple):
                    raise AssertionError(f"Expected tuple, got {type(t)}")
                if len(t) != 2:
                    raise AssertionError(f"Expected tuple of length 2, got {len(t)}")

            test_case_inst.assertEqual(
                x[0],
                y[0],
                atol=atol,
                rtol=rtol,
                equal_nan=equal_nan,
                exact_dtype=exact_dtype,
                exact_stride=exact_stride,
            )

            # The second tensor is the same result as an argsort.
            x = x[1]
            y = y[1]

        if exact_dtype and (x.dtype != y.dtype):
            raise AssertionError(f"The dtypes do not match: {x.dtype} != {y.dtype}.")

        if x.shape != y.shape:
            raise AssertionError(f"Shape mismatch: {x.shape} != {y.shape}")

        if exact_stride and (x.stride() != y.stride()):
            raise AssertionError(
                f"The strides do not match: {x.stride()} != {y.stride()}."
            )

        def el_to_indices(el):
            """Turn an element number into a list of indices"""
            indices = [None] * x.dim()
            for cur_dim in reversed(range(x.dim())):
                indices[cur_dim] = el % x.shape[cur_dim]
                el //= x.shape[cur_dim]
            if None in indices:
                raise AssertionError("indices contains None")
            return indices

        def get_val_by_ids(t, ids):
            """Return a value from a tensor at a given list of indices"""
            for idx in ids:
                t = t[idx]
            return t.item()

        # Loop through every value of the tensors and check for equality or
        # compatibility.
        for current_el in range(x.numel()):
            ids = el_to_indices(current_el)

            # Simple case: check equality of arsort indices
            if get_val_by_ids(x, ids) == get_val_by_ids(y, ids):
                continue

            # Complex case: check if indices refer to same value
            x_orig_ids = ids.copy()
            y_orig_ids = ids.copy()

            x_orig_ids[dim] = get_val_by_ids(x, ids)
            y_orig_ids[dim] = get_val_by_ids(y, ids)

            x_value = get_val_by_ids(orig_input, x_orig_ids)
            y_value = get_val_by_ids(orig_input, y_orig_ids)
            if x_value == y_value:
                continue

            if equal_nan:
                if math.isnan(x_value) and math.isnan(y_value):
                    continue

            raise AssertionError(
                f"Non-stable argsort outputs are incompatible at {ids}"
            )