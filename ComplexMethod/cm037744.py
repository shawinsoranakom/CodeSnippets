def _chunk_scan_fwd(
    cb,
    x,
    dt,
    dA_cumsum,
    C,
    states,
    cu_chunk_seqlens,
    out,
    seq_idx,
    D=None,
    z=None,
    initial_states=None,
):
    assert seq_idx is not None, "this implementation requires seq_idx"

    seqlen, nheads, headdim = x.shape
    _, nchunks, chunk_size = dt.shape
    _, ngroups, dstate = C.shape
    assert nheads % ngroups == 0
    assert C.shape == (seqlen, ngroups, dstate)
    assert cb.shape == (nchunks, ngroups, chunk_size, chunk_size)
    if D is not None:
        assert D.shape == (nheads, headdim) or D.shape == (nheads,)
    if z is not None:
        assert z.shape == x.shape
    assert dt.shape == (nheads, nchunks, chunk_size)
    assert dA_cumsum.shape == (nheads, nchunks, chunk_size)
    assert states.shape == (nchunks, nheads, headdim, dstate)
    assert seq_idx.shape == (nchunks,)

    grid = lambda META: (
        triton.cdiv(chunk_size, META["BLOCK_SIZE_M"])
        * triton.cdiv(headdim, META["BLOCK_SIZE_N"]),
        nchunks,
        nheads,
    )

    z_strides = (z.stride(0), z.stride(1), z.stride(2)) if z is not None else (0, 0, 0)
    initial_states_strides = (
        (
            initial_states.stride(0),
            initial_states.stride(1),
            initial_states.stride(2),
            initial_states.stride(3),
        )
        if initial_states is not None
        else (0, 0, 0, 0)
    )

    _chunk_scan_fwd_kernel[grid](
        cb_ptr=cb,
        x_ptr=x,
        z_ptr=z,
        out_ptr=out,
        dt_ptr=dt,
        dA_cumsum_ptr=dA_cumsum,
        seq_idx_ptr=seq_idx,
        C_ptr=C,
        states_ptr=states,
        D_ptr=D,
        initstates_ptr=initial_states,
        cu_chunk_seqlens_ptr=cu_chunk_seqlens,
        chunk_size=chunk_size,
        hdim=headdim,
        dstate=dstate,
        seqlen=seqlen,
        nheads_ngroups_ratio=nheads // ngroups,
        stride_cb_chunk=cb.stride(0),
        stride_cb_head=cb.stride(1),
        stride_cb_csize_m=cb.stride(2),
        stride_cb_csize_k=cb.stride(3),
        stride_x_seqlen=x.stride(0),
        stride_x_head=x.stride(1),
        stride_x_hdim=x.stride(2),
        stride_z_seqlen=z_strides[0],
        stride_z_head=z_strides[1],
        stride_z_hdim=z_strides[2],
        stride_out_seqlen=out.stride(0),
        stride_out_head=out.stride(1),
        stride_out_hdim=out.stride(2),
        stride_dt_chunk=dt.stride(1),
        stride_dt_head=dt.stride(0),
        stride_dt_csize=dt.stride(2),
        stride_dA_cs_chunk=dA_cumsum.stride(1),
        stride_dA_cs_head=dA_cumsum.stride(0),
        stride_dA_cs_csize=dA_cumsum.stride(2),
        stride_seq_idx_chunk=seq_idx.stride(0),
        stride_C_seqlen=C.stride(0),
        stride_C_head=C.stride(1),
        stride_C_dstate=C.stride(2),
        stride_states_chunk=states.stride(0),
        stride_states_head=states.stride(1),
        stride_states_hdim=states.stride(2),
        stride_states_dstate=states.stride(3),
        stride_init_states_batch=initial_states_strides[0],
        stride_init_states_head=initial_states_strides[1],
        stride_init_states_hdim=initial_states_strides[2],
        stride_init_states_dstate=initial_states_strides[3],
        stride_D_head=D.stride(0) if D is not None else 0,
        IS_CAUSAL=True,
        HAS_D=D is not None,
        D_HAS_HDIM=D.dim() == 2 if D is not None else True,
        HAS_Z=z is not None,
        BLOCK_SIZE_DSTATE=max(triton.next_power_of_2(dstate), 16),
        IS_TRITON_22=TRITON_22,
        HAS_INITSTATES=initial_states is not None,
    )
    return