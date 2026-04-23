def test_out(self, device, dtype, op):
        # Prefers running in float32 but has a fallback for the first listed supported dtype
        samples = op.sample_inputs(device, dtype)

        # Ops from python_ref_db point to python decomps that are potentially
        # wrapped with `torch._prims_common.wrappers.out_wrapper`. Unwrap these
        # ops before testing to avoid clashing with OpInfo.supports_out
        if not op.supports_out:
            op = copy.copy(op)
            op.op = _maybe_remove_out_wrapper(op.op)

        for sample in samples:
            # calls it normally to get the expected result
            expected = op(sample.input, *sample.args, **sample.kwargs)
            op_out = partial(op, sample.input, *sample.args, **sample.kwargs)

            # Short-circuits if output is not a single tensor or an
            #   iterable of tensors
            if not isinstance(expected, torch.Tensor) and not is_iterable_of_tensors(
                expected, include_empty=True
            ):
                self.skipTest(
                    "Skipped! Only supports single tensor or iterable of tensor outputs."
                )

            # Validates the op doesn't support out if it claims not to
            if not op.supports_out:
                with self.assertRaises(Exception):
                    if op_out(out=expected) == NotImplemented:
                        raise AssertionError("op_out returned NotImplemented")
                return

            # A wrapper around map that works with single tensors and always
            #   instantiates the map. Used below to apply transforms to
            #   single tensor and iterable tensor outputs.
            def _apply_out_transform(fn, out):
                if isinstance(out, torch.Tensor):
                    return fn(out)

                # assumes (see above) that out is an iterable of tensors
                return tuple(map(fn, out))

            # Extracts strides from a tensor or iterable of tensors into a tuple
            def _extract_strides(out):
                if isinstance(out, torch.Tensor):
                    return (out.stride(),)

                # assumes (see above) that out is an iterable of tensors
                return tuple(t.stride() for t in out)

            # Extracts data pointers from a tensor or iterable of tensors into a tuple
            # NOTE: only extracts on the CPU and CUDA device types since some
            #   device types don't have storage
            def _extract_data_ptrs(out):
                if self.device_type != "cpu" and self.device_type != "cuda":
                    return ()

                if isinstance(out, torch.Tensor):
                    return (out.data_ptr(),)

                # assumes (see above) that out is an iterable of tensors
                return tuple(t.data_ptr() for t in out)

            def _compare_out(transform, *, compare_strides_and_data_ptrs=True):
                out = _apply_out_transform(transform, expected)
                original_strides = _extract_strides(out)
                original_ptrs = _extract_data_ptrs(out)

                op_out(out=out)
                final_strides = _extract_strides(out)
                final_ptrs = _extract_data_ptrs(out)
                self.assertEqual(expected, out)

                if compare_strides_and_data_ptrs:
                    stride_msg = (
                        "Strides are not the same! "
                        f"Original strides were {original_strides} and strides are now {final_strides}"
                    )
                    self.assertEqual(original_strides, final_strides, msg=stride_msg)
                    self.assertEqual(original_ptrs, final_ptrs)

            # Case 0: out= with the correct shape, dtype, and device
            #   but NaN values for floating point and complex tensors, and
            #   maximum values for integer tensors.
            #   Expected behavior: out= values have no effect on the computation.
            def _case_zero_transform(t):
                try:
                    info = torch.iinfo(t.dtype)
                    return torch.full_like(t, info.max)
                except TypeError:
                    # for non-integer types fills with NaN
                    return torch.full_like(t, float("nan"))

            _compare_out(_case_zero_transform)

            # Case 1: out= with the correct shape, dtype, and device,
            #   but noncontiguous.
            #   Expected behavior: strides are respected and `out` storage is not changed.
            def _case_one_transform(t):
                return make_tensor(
                    t.shape, dtype=t.dtype, device=t.device, noncontiguous=True
                )

            _compare_out(_case_one_transform)

            # Case 2: out= with the correct dtype and device, but has no elements.
            #   Expected behavior: resize without warning.
            def _case_two_transform(t):
                return make_tensor((0,), dtype=t.dtype, device=t.device)

            _compare_out(_case_two_transform, compare_strides_and_data_ptrs=False)

            # Also validates that no warning is thrown when this out is resized
            out = _apply_out_transform(_case_two_transform, expected)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                op_out(out=out)

            # Verifies no warning is a resize warning
            for w in caught:
                if "An output with one or more elements" in str(w.message):
                    self.fail(
                        "Resizing an out= argument with no elements threw a resize warning!"
                    )

            # Case 3: out= with correct shape and dtype, but wrong device.
            #   Expected behavior: throws an error.
            #   This case is ignored on CPU to allow some scalar operations to succeed.
            factory_fn_msg = (
                "\n\nNOTE: If your op is a factory function (i.e., it accepts TensorOptions) you should mark its "
                "OpInfo with `is_factory_function=True`."
            )

            if torch.device(device).type != "cpu":
                wrong_device = "cpu"

                def _case_three_transform(t):
                    return make_tensor(t.shape, dtype=t.dtype, device=wrong_device)

                out = _apply_out_transform(_case_three_transform, expected)

                if op.is_factory_function and sample.kwargs.get("device", None) is None:
                    op_out(out=out)
                else:
                    msg_fail = (
                        f"Expected RuntimeError when calling with input.device={device} and out.device={wrong_device}."
                    ) + factory_fn_msg
                    with self.assertRaises(RuntimeError, msg=msg_fail):
                        op_out(out=out)

            # Case 4: out= with correct shape and device, but a dtype
            #   that output cannot be "safely" cast to (long).
            #   Expected behavior: error.
            # NOTE: this case is filtered by dtype since some ops produce
            #   bool tensors, for example, which can be safely cast to any
            #   dtype. It is applied when single tensors are floating point or complex
            #   dtypes, or if an op returns multiple tensors when at least one such
            #   tensor is a floating point or complex dtype.
            _dtypes = floating_and_complex_types_and(torch.float16, torch.bfloat16)
            if (
                isinstance(expected, torch.Tensor)
                and expected.dtype in _dtypes
                or (
                    not isinstance(expected, torch.Tensor)
                    and any(t.dtype in _dtypes for t in expected)
                )
            ):

                def _case_four_transform(t):
                    return make_tensor(t.shape, dtype=torch.long, device=t.device)

                out = _apply_out_transform(_case_four_transform, expected)
                msg_fail = "Expected RuntimeError when doing an unsafe cast!"
                msg_fail = (
                    msg_fail
                    if not isinstance(expected, torch.Tensor)
                    else (
                        "Expected RuntimeError when doing an unsafe cast from a result of dtype "
                        f"{expected.dtype} into an out= with dtype torch.long"
                    )
                ) + factory_fn_msg

                if op.is_factory_function and sample.kwargs.get("dtype", None) is None:
                    op_out(out=out)
                else:
                    # TODO: Remove me when all ops will raise type error on mismatched types
                    exc_type = (
                        TypeError
                        if op.name
                        in [
                            "_chunk_cat",
                            "cat",
                            "column_stack",
                            "dstack",
                            "hstack",
                            "vstack",
                            "stack",
                        ]
                        else RuntimeError
                    )
                    with self.assertRaises(exc_type, msg=msg_fail):
                        op_out(out=out)