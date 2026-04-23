def _test_undefined_backward_mode(func, outputs, inputs) -> bool:
    diff_input_list: list[torch.Tensor] = list(_iter_tensors(inputs, True))
    if not diff_input_list:
        raise GradcheckError("no Tensors requiring grad found in input")

    def warn_bc_breaking():
        warnings.warn(
            "Backwards compatibility: New undefined gradient support checking "
            "feature is enabled by default, but it may break existing callers "
            "of this function. If this is true for you, you can call this "
            'function with "check_undefined_grad=False" to disable the feature',
            stacklevel=2,
        )

    def check_undefined_grad_support(output_to_check):
        grads_output = [
            torch.zeros_like(o, memory_format=torch.legacy_contiguous_format)
            for o in output_to_check
        ]
        try:
            grads_input = torch.autograd.grad(
                output_to_check, diff_input_list, grads_output, allow_unused=True
            )
        except RuntimeError as e:
            warn_bc_breaking()
            raise GradcheckError(
                "Expected backward function to handle undefined output grads. "
                'Please look at "Notes about undefined output gradients" in '
                '"tools/autograd/derivatives.yaml"'
            ) from e

        for gi in grads_input:
            if (gi is not None) and (not gi.eq(0).all()):
                warn_bc_breaking()
                raise GradcheckError(
                    "Expected all input grads to be undefined or zero when all output grads are undefined "
                    'or zero. Please look at "Notes about undefined output gradients" in '
                    '"tools/autograd/derivatives.yaml"'
                )
        return True

    # All backward functions must work properly if all output grads are undefined
    outputs_to_check = [
        [
            torch._C._functions.UndefinedGrad()(o)
            for o in _differentiable_outputs(func(*inputs))
            # This check filters out Tensor-likes that aren't instances of Tensor.
            if isinstance(o, torch.Tensor)
        ]
    ]

    # If there are multiple output grads, we should be able to undef one at a time without error
    if len(outputs_to_check[0]) > 1:
        for undef_grad_idx in range(len(outputs)):
            output_to_check = _differentiable_outputs(func(*inputs))
            outputs_to_check.append(
                [
                    torch._C._functions.UndefinedGrad()(o)
                    if idx == undef_grad_idx
                    else o
                    for idx, o in enumerate(output_to_check)
                ]
            )

    return all(check_undefined_grad_support(output) for output in outputs_to_check)