def check_model_gpu(
    self: TestCase,
    model,
    example_inputs,
    kwargs=None,
    *,
    atol=None,
    rtol=None,
    grad_atol=None,
    grad_rtol=None,
    check_lowp=True,
    exact_dtype=True,
    nopython=True,
    copy_to_gpu=True,
    reference_in_float=True,
    assert_equal=True,
    check_gradient=False,
    check_has_compiled=True,
    output_process_fn_grad=lambda x: x,
    # TODO: enable this for all tests
    exact_stride=False,
):
    kwargs = kwargs or {}
    if hasattr(model, "to"):
        model = model.to(device=GPU_TYPE)

    if copy_to_gpu:
        example_inputs = tuple(
            clone_preserve_strides_offset(x, device=GPU_TYPE) for x in example_inputs
        )

    check_model(
        self,
        model,
        example_inputs,
        kwargs,
        atol=atol,
        rtol=rtol,
        grad_atol=grad_atol,
        grad_rtol=grad_rtol,
        exact_dtype=exact_dtype,
        nopython=nopython,
        reference_in_float=reference_in_float,
        assert_equal=assert_equal,
        check_gradient=check_gradient,
        check_has_compiled=check_has_compiled,
        output_process_fn_grad=output_process_fn_grad,
        exact_stride=exact_stride,
    )

    if check_lowp:

        def downcast_fn(x):
            if not isinstance(x, torch.Tensor) or x.dtype != torch.float:
                return x
            return torch.empty_strided(
                x.size(), x.stride(), device=GPU_TYPE, dtype=torch.half
            ).copy_(x)

        example_inputs = list(map(downcast_fn, example_inputs))
        if hasattr(model, "to"):
            model = model.to(torch.half)
        if rtol is not None:
            rtol = max(2e-3, rtol)
        check_model(
            self,
            model,
            example_inputs,
            kwargs,
            atol=atol,
            rtol=rtol,
            grad_atol=grad_atol,
            grad_rtol=grad_rtol,
            exact_dtype=exact_dtype,
            nopython=nopython,
            reference_in_float=reference_in_float,
            assert_equal=assert_equal,
            check_gradient=check_gradient,
            check_has_compiled=check_has_compiled,
            output_process_fn_grad=output_process_fn_grad,
            exact_stride=exact_stride,
        )