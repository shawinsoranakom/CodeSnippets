def _compute_numerical_jvps_wrt_specific_input(
    jvp_fn, delta, input_is_complex, is_forward_ad=False
) -> list[torch.Tensor]:
    # Computing the jacobian only works for real delta
    # For details on the algorithm used here, refer:
    # Section 3.5.3 https://arxiv.org/pdf/1701.00392.pdf
    # s = fn(z) where z = x for real valued input
    # and z = x + yj for complex valued input
    jvps: list[torch.Tensor] = []
    ds_dx_tup = jvp_fn(delta[0] if isinstance(delta, tuple) else delta)

    if input_is_complex:  # C -> R
        ds_dy_tup = (
            jvp_fn(delta[1] * 1j) if isinstance(delta, tuple) else jvp_fn(delta * 1j)
        )
        for ds_dx, ds_dy in zip(ds_dx_tup, ds_dy_tup):
            if ds_dx.is_complex():
                raise AssertionError("Expected ds_dx to be real-valued, not complex")
            # conjugate wirtinger derivative
            conj_w_d = ds_dx + ds_dy * 1j
            jvps.append(conj_w_d)
    else:
        for ds_dx in ds_dx_tup:  # R -> R or (R -> C for the forward AD case)
            if not is_forward_ad and ds_dx.is_complex():
                raise AssertionError("Expected ds_dx to be real-valued, not complex.")
            jvps.append(ds_dx)
    return jvps