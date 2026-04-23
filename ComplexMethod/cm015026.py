def _ref_test_helper(
        self,
        ctx,
        device,
        dtype,
        op,
        skip_zero_numel=False,
        skip_zero_dim=False,
        skip_bfloat=False,
        skip_view_consistency=False,
    ):
        # NOTE: this test works by comparing the reference
        for sample in op.reference_inputs(device, dtype, requires_grad=False):
            ex = None
            if (
                isinstance(sample.input, torch.Tensor)
                and sample.input.numel() == 0
                and skip_zero_numel
            ):
                continue
            if (
                isinstance(sample.input, torch.Tensor)
                and sample.input.ndim == 0
                and skip_zero_dim
            ):
                continue

            if skip_bfloat and (
                (
                    isinstance(sample.input, torch.Tensor)
                    and sample.input.dtype == torch.bfloat16
                )
                or any(
                    isinstance(arg, torch.Tensor) and arg.dtype == torch.bfloat16
                    for arg in sample.args
                )
            ):
                continue
            with ctx():
                ref_result = op(sample.input, *sample.args, **sample.kwargs)
            torch_result = op.torch_opinfo(sample.input, *sample.args, **sample.kwargs)

            for a, b in zip(
                pytree.tree_leaves(ref_result), pytree.tree_leaves(torch_result)
            ):
                if isinstance(a, torch.Tensor) or isinstance(b, torch.Tensor):
                    prims.utils.compare_tensor_meta(a, b)
                    if (
                        getattr(op, "validate_view_consistency", True)
                        and not skip_view_consistency
                    ):
                        msg = (
                            f"The torch implementation {'returns' if b._is_view() else 'does not return'} "
                            f"a view, while the reference {'does' if a._is_view() else 'does not'}"
                        )
                        self.assertEqual(a._is_view(), b._is_view(), msg)

            # Computes the dtype the more precise computatino would occur in
            precise_dtype = torch.bool
            if prims.utils.is_integer_dtype(dtype):
                # Note: bool and integer dtypes do not have more
                # precise dtypes -- they simply must be close
                precise_dtype = dtype
            if prims.utils.is_float_dtype(dtype):
                precise_dtype = highest_precision_float(device)
            if prims.utils.is_complex_dtype(dtype):
                precise_dtype = (
                    torch.complex32
                    if torch.device(device).type == "mps"
                    else torch.cdouble
                )

            # Checks if the results are close
            try:
                self.assertEqual(
                    ref_result,
                    torch_result,
                    exact_stride=False,
                    exact_device=True,
                    exact_layout=True,
                    exact_is_coalesced=True,
                )
            except AssertionError as e:
                # Raises the error if the precise dtype comparison wouldn't be
                # different
                if dtype is precise_dtype:
                    raise e

                ex = e

            # Goes to next sample if these results are close
            if not ex:
                continue

            # If the results are not close, checks that the
            # reference is more accurate than the torch op
            def _make_precise(x):
                if isinstance(x, torch.dtype):
                    return precise_dtype
                if isinstance(x, torch.Tensor) and x.dtype is dtype:
                    return x.to(precise_dtype)
                return x

            precise_sample = sample.transform(_make_precise)
            precise_result = op.torch_opinfo(
                precise_sample.input, *precise_sample.args, **precise_sample.kwargs
            )

            def _distance(a, b):
                # Special-cases boolean comparisons
                if prims.utils.is_boolean_dtype(a.dtype):
                    if b.dtype is not torch.bool:
                        raise AssertionError(
                            f"expected dtype torch.bool, got {b.dtype}"
                        )
                    return (a ^ b).sum()

                same = a == b
                if prims.utils.is_float_dtype(a.dtype) or prims.utils.is_complex_dtype(
                    a.dtype
                ):
                    same = torch.logical_or(
                        same, torch.logical_and(torch.isnan(a), torch.isnan(b))
                    )

                actual_error = torch.where(same, 0, torch.abs(a - b)).sum()
                return actual_error

            ref_distance = 0
            for a, b in zip(
                pytree.tree_leaves(ref_result), pytree.tree_leaves(precise_result)
            ):
                ref_distance = ref_distance + _distance(a, b)

            torch_distance = 0
            for a, b in zip(
                pytree.tree_leaves(torch_result), pytree.tree_leaves(precise_result)
            ):
                torch_distance = torch_distance + _distance(a, b)

            # TODO: consider adding some tolerance to this comparison
            msg = (
                f"Reference result was farther ({ref_distance}) from the precise "
                f"computation than the torch result was ({torch_distance})!"
            )
            self.assertTrue(ref_distance <= torch_distance, msg=msg)

        # Reports numerical accuracy discrepancies
        if ex is not None:
            msg = "Test passed because the reference was more accurate than the torch operator."
            warnings.warn(msg)