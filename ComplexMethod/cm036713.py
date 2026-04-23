def test_selective_scan(
    is_variable_B,
    is_variable_C,
    varBC_groups,
    has_D,
    has_z,
    has_delta_bias,
    delta_softplus,
    seqlen,
    itype,
    wtype,
    scan_chunks,
):
    if varBC_groups > 1 and (not is_variable_B or not is_variable_C):
        pytest.skip()  # This config is not applicable
    device = "cuda"
    rtol, atol = (6e-4, 2e-3) if itype == torch.float32 else (3e-3, 5e-3)
    if itype == torch.bfloat16:
        rtol, atol = 3e-2, 5e-2
    rtolw, atolw = (1e-3, 1e-3)
    if has_z:  # If we have z, the errors on the weights seem higher
        rtolw = max(rtolw, rtol)
        atolw = max(atolw, atol)
    # set seed
    set_random_seed(0)
    batch_size = 1
    dim = 4
    dstate = 8
    A = -0.5 * torch.rand(dim, dstate, device=device, dtype=wtype)
    A_ref = A.clone()
    if not is_variable_B:
        B_shape = [dim, dstate]
    elif varBC_groups == 1:
        B_shape = [batch_size, dstate, seqlen]
    else:
        B_shape = [batch_size, varBC_groups, dstate, seqlen]
    B = torch.randn(B_shape, device=device, dtype=wtype if not is_variable_B else itype)
    B_ref = B.clone()
    if not is_variable_C:
        C_shape = [dim, dstate]
    elif varBC_groups == 1:
        C_shape = [batch_size, dstate, seqlen]
    else:
        C_shape = [batch_size, varBC_groups, dstate, seqlen]
    C = torch.randn(C_shape, device=device, dtype=wtype if not is_variable_C else itype)
    C_ref = C.clone()
    D = torch.randn(dim, device=device, dtype=torch.float32) if has_D else None
    D_ref = D.clone() if D is not None else None
    z = (
        torch.randn(batch_size, dim, seqlen, device=device, dtype=itype)
        if has_z
        else None
    )
    z_ref = z.clone() if z is not None else None
    delta_bias = (
        (0.5 * torch.rand(dim, device=device, dtype=torch.float32))
        if has_delta_bias
        else None
    )
    u = torch.randn(batch_size, dim, seqlen, device=device, dtype=itype)
    u_ref = u.clone()
    delta = 0.5 * torch.rand(batch_size, dim, seqlen, device=device, dtype=itype)
    delta_ref = delta.clone()
    state_shape = (batch_size, u.shape[1], int(A.shape[1]))
    state = torch.randn(state_shape, device=u.device, dtype=itype, requires_grad=False)
    state_ref = state.clone()
    out = None
    out_ref = None
    outs = []
    for c in range(scan_chunks):
        chunked_prompt_len = seqlen // scan_chunks
        chunk_start = chunked_prompt_len * c
        chunk_end = chunked_prompt_len * (c + 1)
        if c == scan_chunks - 1:
            chunk_end = seqlen
        _B = B
        if is_variable_B:
            _B = B[..., chunk_start:chunk_end]
        _C = C
        if is_variable_B:
            _C = C[..., chunk_start:chunk_end]
        _z = z
        if has_z:
            assert z is not None
            _z = z[..., chunk_start:chunk_end]
        out = selective_scan_fn(
            u[..., chunk_start:chunk_end],
            state,
            delta[..., chunk_start:chunk_end],
            A,
            _B,
            _C,
            D,
            z=_z,
            delta_bias=delta_bias,
            delta_softplus=delta_softplus,
            has_initial_state=torch.ones(batch_size, device=u.device, dtype=torch.bool)
            if c > 0
            else None,
            block_size=2048,
            block_idx_first_scheduled_token=None,
            block_idx_last_scheduled_token=None,
            initial_state_idx=None,
        )
        outs.append(out)
    if len(outs) > 1:
        out = torch.cat(outs, dim=-1)

    out_ref, state_ref, *rest = selective_scan_ref(
        u_ref,
        delta_ref,
        A_ref,
        B_ref,
        C_ref,
        D_ref,
        z=z_ref,
        delta_bias=delta_bias,
        delta_softplus=delta_softplus,
        return_last_state=True,
    )

    assert out is not None and out_ref is not None
    assert torch.allclose(out, out_ref, rtol=rtol, atol=atol)
    assert state is not None and state_ref is not None
    assert torch.allclose(state, state_ref.to(itype), rtol=rtol, atol=atol)

    selective_scan_opcheck_fn(
        u,
        delta,
        A,
        B,
        C,
        D,
        z,
        delta_bias=delta_bias,
        delta_softplus=delta_softplus,
        ssm_states=state,
        block_size=2048,
    )