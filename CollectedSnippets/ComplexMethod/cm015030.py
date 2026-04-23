def test_dtypes(self, device, op):
        # Check complex32 support only if the op claims.
        # TODO: Once the complex32 support is better, we should add check for complex32 unconditionally.
        device_type = torch.device(device).type
        include_complex32 = (
            (torch.complex32,)
            if op.supports_dtype(torch.complex32, device_type)
            else ()
        )

        # dtypes to try to backward in
        allowed_backward_dtypes = floating_and_complex_types_and(
            *((torch.half, torch.bfloat16) + include_complex32)
        )

        # lists for (un)supported dtypes
        supported_dtypes = set()
        unsupported_dtypes = set()
        supported_backward_dtypes = set()
        unsupported_backward_dtypes = set()
        dtype_error: dict[torch.dtype, Exception] = {}

        def unsupported(dtype, e):
            dtype_error[dtype] = e
            unsupported_dtypes.add(dtype)
            if dtype in allowed_backward_dtypes:
                unsupported_backward_dtypes.add(dtype)

        for dtype in all_types_and_complex_and(
            *((torch.half, torch.bfloat16, torch.bool) + include_complex32)
        ):
            # tries to acquire samples - failure indicates lack of support
            requires_grad = dtype in allowed_backward_dtypes
            try:
                samples = tuple(
                    op.sample_inputs(device, dtype, requires_grad=requires_grad)
                )
            except Exception as e:
                unsupported(dtype, e)
                continue

            for sample in samples:
                # tries to call operator with the sample - failure indicates
                #   lack of support
                try:
                    result = op(sample.input, *sample.args, **sample.kwargs)
                    supported_dtypes.add(dtype)
                except Exception as e:
                    # NOTE: some ops will fail in forward if their inputs
                    #   require grad but they don't support computing the gradient
                    #   in that type! This is a bug in the op!
                    unsupported(dtype, e)
                    continue

                # Checks for backward support in the same dtype, if the input has
                # one or more tensors requiring grad
                def _tensor_requires_grad(x):
                    if isinstance(x, dict):
                        for v in x.values():
                            if _tensor_requires_grad(v):
                                return True
                    if isinstance(x, (list, tuple)):
                        for a in x:
                            if _tensor_requires_grad(a):
                                return True
                    if isinstance(x, torch.Tensor) and x.requires_grad:
                        return True

                    return False

                requires_grad = (
                    _tensor_requires_grad(sample.input)
                    or _tensor_requires_grad(sample.args)
                    or _tensor_requires_grad(sample.kwargs)
                )
                if not requires_grad:
                    continue

                try:
                    result = sample.output_process_fn_grad(result)
                    if isinstance(result, torch.Tensor):
                        backward_tensor = result
                    elif isinstance(result, Sequence) and isinstance(
                        result[0], torch.Tensor
                    ):
                        backward_tensor = result[0]
                    else:
                        continue

                    # Note: this grad may not have the same dtype as dtype
                    # For functions like complex (float -> complex) or abs
                    #   (complex -> float) the grad tensor will have a
                    #   different dtype than the input.
                    #   For simplicity, this is still modeled as these ops
                    #   supporting grad in the input dtype.
                    grad = torch.randn_like(backward_tensor)
                    backward_tensor.backward(grad)
                    supported_backward_dtypes.add(dtype)
                except Exception as e:
                    dtype_error[dtype] = e
                    unsupported_backward_dtypes.add(dtype)

        # Checks that dtypes are listed correctly and generates an informative
        #   error message

        supported_forward = supported_dtypes - unsupported_dtypes
        partially_supported_forward = supported_dtypes & unsupported_dtypes
        unsupported_forward = unsupported_dtypes - supported_dtypes
        supported_backward = supported_backward_dtypes - unsupported_backward_dtypes
        partially_supported_backward = (
            supported_backward_dtypes & unsupported_backward_dtypes
        )
        unsupported_backward = unsupported_backward_dtypes - supported_backward_dtypes

        device_type = torch.device(device).type

        claimed_forward = set(op.supported_dtypes(device_type))
        supported_but_unclaimed_forward = supported_forward - claimed_forward
        claimed_but_unsupported_forward = claimed_forward & unsupported_forward

        claimed_backward = set(op.supported_backward_dtypes(device_type))
        supported_but_unclaimed_backward = supported_backward - claimed_backward
        claimed_but_unsupported_backward = claimed_backward & unsupported_backward

        # Partially supporting a dtype is not an error, but we print a warning
        if (len(partially_supported_forward) + len(partially_supported_backward)) > 0:
            msg = f"Some dtypes for {op.name} on device type {device_type} are only partially supported!\n"
            if len(partially_supported_forward) > 0:
                msg = (
                    msg
                    + f"The following dtypes only worked on some samples during forward: {partially_supported_forward}.\n"
                )
            if len(partially_supported_backward) > 0:
                msg = (
                    msg
                    + f"The following dtypes only worked on some samples during backward: {partially_supported_backward}.\n"
                )
            print(msg)

        if (
            len(supported_but_unclaimed_forward)
            + len(claimed_but_unsupported_forward)
            + len(supported_but_unclaimed_backward)
            + len(claimed_but_unsupported_backward)
        ) == 0:
            return

        if TEST_WITH_TORCHDYNAMO:
            # NOTE: Also for TEST_WITH_TORCHINDUCTOR tests
            # Under compile, some ops may be decomposed into supported ops
            # So it is okay to have supported_but_unclaimed_*
            if (
                len(claimed_but_unsupported_forward)
                + len(claimed_but_unsupported_backward)
            ) == 0:
                return

        # Reference operators often support additional dtypes, and that's OK
        if op in python_ref_db:
            if (
                len(claimed_but_unsupported_forward)
                + len(claimed_but_unsupported_backward)
            ) == 0:
                return

        # Generates error msg
        msg = f"The supported dtypes for {op.name} on device type {device_type} are incorrect!\n"
        if len(supported_but_unclaimed_forward) > 0:
            msg = (
                msg
                + "The following dtypes worked in forward but are not listed by the OpInfo: "
                + f"{supported_but_unclaimed_forward}.\n"
            )
        if len(supported_but_unclaimed_backward) > 0:
            msg = (
                msg
                + "The following dtypes worked in backward but are not listed by the OpInfo: "
                + f"{supported_but_unclaimed_backward}.\n"
            )
        if len(claimed_but_unsupported_forward) > 0:
            msg = (
                msg
                + "The following dtypes did not work in forward but are listed by the OpInfo: "
                + f"{claimed_but_unsupported_forward}.\n"
            )
        if len(claimed_but_unsupported_backward) > 0:
            msg = (
                msg
                + "The following dtypes did not work in backward "
                + f"but are listed by the OpInfo: {claimed_but_unsupported_backward}.\n"
            )

        all_claimed_but_unsupported = set.union(
            claimed_but_unsupported_backward, claimed_but_unsupported_forward
        )
        if all_claimed_but_unsupported:
            msg += "Unexpected failures raised the following errors:\n"
            for dtype in all_claimed_but_unsupported:
                msg += f"{dtype} - {dtype_error[dtype]}\n"

        self.fail(msg)