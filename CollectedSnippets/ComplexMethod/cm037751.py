def _chunk_state_fwd(
    B, x, dt, dA_cumsum, cu_chunk_seqlens, states=None, states_in_fp32=True
):
    seqlen, nheads, headdim = x.shape
    _, nchunks, chunk_size = dt.shape
    _, ngroups, dstate = B.shape
    assert nheads % ngroups == 0
    assert B.shape == (seqlen, ngroups, dstate)
    assert dt.shape == (nheads, nchunks, chunk_size)
    assert dA_cumsum.shape == dt.shape

    if states is not None:
        assert states.shape == (nchunks, nheads, headdim, dstate)
    else:
        states_dtype = torch.float32 if states_in_fp32 else B.dtype
        states = torch.empty(
            (nchunks, nheads, headdim, dstate), device=x.device, dtype=states_dtype
        )

    grid = lambda META: (
        triton.cdiv(headdim, META["BLOCK_SIZE_M"])
        * triton.cdiv(dstate, META["BLOCK_SIZE_N"]),
        nchunks,
        nheads,
    )
    with torch.accelerator.device_index(x.device.index):
        _chunk_state_fwd_kernel[grid](
            x_ptr=x,
            b_ptr=B,
            states_ptr=states,
            dt_ptr=dt,
            dA_cumsum_ptr=dA_cumsum,
            cu_chunk_seqlens_ptr=cu_chunk_seqlens,
            hdim=headdim,
            dstate=dstate,
            chunk_size=chunk_size,
            seqlen=seqlen,
            nheads_ngroups_ratio=nheads // ngroups,
            stride_x_seqlen=x.stride(0),
            stride_x_head=x.stride(1),
            stride_x_hdim=x.stride(2),
            stride_b_seqlen=B.stride(0),
            stride_b_head=B.stride(1),
            stride_b_dstate=B.stride(2),
            stride_states_chunk=states.stride(0),
            stride_states_head=states.stride(1),
            stride_states_hdim=states.stride(2),
            stride_states_dstate=states.stride(3),
            stride_dt_head=dt.stride(0),
            stride_dt_chunk=dt.stride(1),
            stride_dt_csize=dt.stride(2),
            stride_dA_cs_head=dA_cumsum.stride(0),
            stride_dA_cs_chunk=dA_cumsum.stride(1),
            stride_dA_cs_csize=dA_cumsum.stride(2),
        )
    return states