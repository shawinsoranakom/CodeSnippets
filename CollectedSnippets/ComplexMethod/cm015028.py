def test_out_warning(self, device, op):
        if TEST_WITH_TORCHDYNAMO and op.name == "_refs.clamp":
            self.skipTest("flaky")
        # Prefers running in float32 but has a fallback for the first listed supported dtype
        supported_dtypes = op.supported_dtypes(self.device_type)
        if len(supported_dtypes) == 0:
            self.skipTest("Skipped! Op has not supported dtypes on this device.")
        dtype = (
            torch.float32
            if torch.float32 in supported_dtypes
            else next(iter(supported_dtypes))
        )

        # Ops from python_ref_db point to python decomps that are potentially
        # wrapped with `torch._prims_common.wrappers.out_wrapper`. Unwrap these
        # ops before testing to avoid clashing with OpInfo.supports_out
        if not op.supports_out:
            op = copy.copy(op)
            op.op = _maybe_remove_out_wrapper(op.op)

        samples = op.sample_inputs(device, dtype)
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

            @suppress_warnings
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
                        f"Strides are not the same! Original strides were {original_strides} "
                        f"and strides are now {final_strides}"
                    )
                    self.assertEqual(original_strides, final_strides, msg=stride_msg)
                    self.assertEqual(original_ptrs, final_ptrs)

            # Case Zero: out= with the correct dtype and device, but the wrong shape
            #   Expected behavior: if nonempty, resize with a warning.
            def _case_zero_transform(t):
                wrong_shape = list(t.shape)

                if len(wrong_shape) == 0:
                    # Handles scalar tensor case (empty list)
                    wrong_shape = [2]
                else:
                    wrong_shape[-1] = wrong_shape[-1] + 1
                return make_tensor(wrong_shape, dtype=t.dtype, device=t.device)

            # Verifies the out values are correct
            _compare_out(_case_zero_transform, compare_strides_and_data_ptrs=False)

            # Additionally validates that the appropriate warning is thrown if a nonempty
            #   tensor is resized.
            def _any_nonempty(out):
                if isinstance(out, torch.Tensor):
                    return out.numel() > 0

                return any(x.numel() > 0 for x in out)

            out = _apply_out_transform(_case_zero_transform, expected)
            msg_fail = "Resized a non-empty tensor but did not warn about it."
            if _any_nonempty(out):
                with self.assertWarnsRegex(
                    UserWarning, "An output with one or more elements", msg=msg_fail
                ):
                    op_out(out=out)