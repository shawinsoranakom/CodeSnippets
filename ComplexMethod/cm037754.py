def selective_state_update(
    state,
    x,
    dt,
    A,
    B,
    C,
    D,
    dt_bias,
    z=None,
    dt_softplus=False,
    state_batch_indices=None,
    dst_state_batch_indices=None,
    null_block_id=NULL_BLOCK_ID,
    out=None,
    num_accepted_tokens=None,
    cu_seqlens=None,
    is_blackwell=False,
    enable_stochastic_rounding=False,
    cache_philox_rounds=0,
):
    """
    Argument:
        state: (batch, dim, dstate) or (batch, nheads, dim, dstate)
        x: (batch, dim) or (batch, nheads, dim)
        dt: (batch, dim) or (batch, nheads, dim)
        A: (dim, dstate) or (nheads, dim, dstate)
        B: (batch, dstate) or (batch, ngroups, dstate)
        C: (batch, dstate) or (batch, ngroups, dstate)
        D: (dim,) or (nheads, dim)
        z: (batch, dim) or (batch, nheads, dim)
        dt_bias: (dim,) or (nheads, dim)
        null_block_id: int
            if state_batch_indices is passed, lets the kernel identify
            padded entries that will not be processed,
            for example: state_batch_indices = [null_block_id, 1, 20,
            null_block_id] in this case, the kernel will not process
            entries at indices 0 and 3
        out: Preallocated ssm output tensor. Assume same shape as x.
             In-place updated.
        num_accepted_tokens: (batch,)
            number of accepted tokens from previous verification step,
            tells the kernel which initial state to use
        cu_seqlens: (batch,)
            length per sequence, for variable length in speculative decoding cases
    """
    if state.dim() == 3:
        state = state.unsqueeze(1)
    if x.dim() == 2:
        x = x.unsqueeze(1)
    if dt.dim() == 2:
        dt = dt.unsqueeze(1)
    if A.dim() == 2:
        A = A.unsqueeze(0)
    if B.dim() == 2:
        B = B.unsqueeze(1)
    if C.dim() == 2:
        C = C.unsqueeze(1)
    if D.dim() == 1:
        D = D.unsqueeze(0)
    if z is not None and z.dim() == 2:
        z = z.unsqueeze(1)
    if dt_bias.dim() == 1:
        dt_bias = dt_bias.unsqueeze(0)
    if out.dim() == 2:
        out = out.unsqueeze(1)
    if state_batch_indices is not None and state_batch_indices.dim() == 1:
        state_batch_indices = state_batch_indices.unsqueeze(1)
    if dst_state_batch_indices is not None and dst_state_batch_indices.dim() == 1:
        dst_state_batch_indices = dst_state_batch_indices.unsqueeze(1)
    if num_accepted_tokens is not None:
        assert state_batch_indices is not None and state_batch_indices.dim() == 2
        assert dst_state_batch_indices is None or dst_state_batch_indices.dim() == 2

    _, nheads, dim, dstate = state.shape
    batch = x.shape[0]
    if cu_seqlens is not None:
        N = len(cu_seqlens) - 1
        # Only used to verify the shape of
        # state_batch_indices and dst_state_batch_indices
        max_seqlen = (
            state_batch_indices.size(-1) if state_batch_indices is not None else 1
        )
    else:
        N = batch
        max_seqlen = 1

    assert x.shape == (batch, nheads, dim)
    assert dt.shape == x.shape
    assert A.shape == (nheads, dim, dstate)
    ngroups = B.shape[1]
    assert nheads % ngroups == 0, "nheads must be divisible by ngroups"
    assert B.shape == (batch, ngroups, dstate)
    assert C.shape == B.shape
    assert D.shape == (nheads, dim)
    if z is not None:
        assert z.shape == x.shape
    assert dt_bias.shape == (nheads, dim)
    if state_batch_indices is not None:
        assert state_batch_indices.shape[0] >= N
        assert state_batch_indices.shape[1] >= max_seqlen
    if dst_state_batch_indices is not None:
        assert dst_state_batch_indices.shape[0] >= N
        assert dst_state_batch_indices.shape[1] >= max_seqlen
    else:
        # revert to the default behavior of in-place state updates
        dst_state_batch_indices = state_batch_indices
    assert out.shape == x.shape
    if num_accepted_tokens is not None:
        assert num_accepted_tokens.shape == (N,)

    grid = lambda META: (triton.cdiv(dim, META["BLOCK_SIZE_M"]), N, nheads)
    z_strides = (z.stride(0), z.stride(1), z.stride(2)) if z is not None else (0, 0, 0)
    state_batch_indices_strides = (
        (state_batch_indices.stride(0), state_batch_indices.stride(1))
        if state_batch_indices is not None
        else (0, 0)
    )
    dst_state_batch_indices_strides = (
        (dst_state_batch_indices.stride(0), dst_state_batch_indices.stride(1))
        if dst_state_batch_indices is not None
        else (0, 0)
    )
    # We don't want autotune since it will overwrite the state.
    # We instead tune by hand based on dstate.

    # Default
    BLOCK_SIZE_M, num_warps = 4, 8

    if dstate <= 16:
        BLOCK_SIZE_M, num_warps = 32, 4
    elif dstate <= 32:
        BLOCK_SIZE_M, num_warps = 16, 4
    elif dstate <= 64:
        BLOCK_SIZE_M, num_warps = 8, 4
    else:
        # dstate > 64
        if is_blackwell:
            # Optimized for B200 with dstate>64
            BLOCK_SIZE_M, num_warps = 32, 8
        elif dstate <= 128:
            BLOCK_SIZE_M, num_warps = 4, 4

    tie_hdim = (
        A.stride(-1) == 0
        and A.stride(-2) == 0
        and dt.stride(-1) == 0
        and dt_bias.stride(-1) == 0
    )
    rand_seed = (
        torch.randint(0, 2**32, (1,), device=state.device)
        if enable_stochastic_rounding
        else None
    )

    with torch.accelerator.device_index(x.device.index):
        _selective_scan_update_kernel[grid](
            state,
            rand_seed,
            x,
            dt,
            dt_bias,
            A,
            B,
            C,
            D,
            z,
            out,
            state_batch_indices,
            dst_state_batch_indices,
            null_block_id,
            num_accepted_tokens,
            cu_seqlens,
            N,
            nheads,
            dim,
            dstate,
            nheads // ngroups,
            state.stride(0),
            state.stride(1),
            state.stride(2),
            state.stride(3),
            x.stride(0),
            x.stride(1),
            x.stride(2),
            dt.stride(0),
            dt.stride(1),
            dt.stride(2),
            dt_bias.stride(0),
            dt_bias.stride(1),
            A.stride(0),
            A.stride(1),
            A.stride(2),
            B.stride(0),
            B.stride(1),
            B.stride(2),
            C.stride(0),
            C.stride(1),
            C.stride(2),
            D.stride(0),
            D.stride(1),
            z_strides[0],
            z_strides[1],
            z_strides[2],
            out.stride(0),
            out.stride(1),
            out.stride(2),
            state_batch_indices_strides[0],
            state_batch_indices_strides[1],
            dst_state_batch_indices_strides[0],
            dst_state_batch_indices_strides[1],
            dt_softplus,
            tie_hdim,
            BLOCK_SIZE_M,
            num_warps=num_warps,
            USE_RS_ROUNDING=enable_stochastic_rounding,
            PHILOX_ROUNDS=cache_philox_rounds,
        )