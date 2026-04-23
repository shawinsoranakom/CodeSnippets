def _slow_gradcheck(
    func,
    func_out,
    tupled_inputs,
    outputs,
    eps,
    rtol,
    atol,
    check_grad_dtypes,
    nondet_tol,
    *,
    use_forward_ad=False,
    complex_indices=None,
    test_imag=False,
    masked=False,
):
    func_out = _as_tuple(func_out)
    if not outputs:
        return _check_no_differentiable_outputs(
            func, tupled_inputs, func_out, eps=eps, is_forward_ad=use_forward_ad
        )
    tupled_inputs_numerical = tupled_inputs if masked else _densify(tupled_inputs)

    numerical = _transpose(
        _get_numerical_jacobian(
            func,
            tupled_inputs_numerical,
            func_out,
            eps=eps,
            is_forward_ad=use_forward_ad,
        )
    )
    # Note: [numerical vs analytical output length]
    # The numerical path returns jacobian quantity for all outputs, even if requires_grad of that
    # output is False. This behavior is necessary for _check_no_differentiable_outputs to work.
    numerical = [nj for o, nj in zip(func_out, numerical) if o.requires_grad]
    if use_forward_ad:
        analytical_forward = _get_analytical_jacobian_forward_ad(
            func, tupled_inputs, func_out, check_grad_dtypes=check_grad_dtypes
        )

        for i, n_per_out in enumerate(numerical):
            for j, n in enumerate(n_per_out):
                a = analytical_forward[j][i]
                if not _allclose_with_type_promotion(a, n.to(a.device), rtol, atol):
                    raise GradcheckError(
                        _get_notallclose_msg(
                            a, n, i, j, complex_indices, test_imag, is_forward_ad=True
                        )
                    )
    else:
        for i, o in enumerate(outputs):
            analytical = _check_analytical_jacobian_attributes(
                tupled_inputs, o, nondet_tol, check_grad_dtypes
            )

            for j, (a, n) in enumerate(zip(analytical, numerical[i])):
                if not _allclose_with_type_promotion(a, n.to(a.device), rtol, atol):
                    raise GradcheckError(
                        _get_notallclose_msg(a, n, i, j, complex_indices, test_imag)
                    )

    return True