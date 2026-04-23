def _bmm_chunk_fwd(a, b, chunk_size, cu_chunk_seqlens, causal=False, output_dtype=None):
    """
    Argument:
        a: (seqlen, ngroups, k)
        b: (seqlen, ngroups, k)
        chunk_size: int
        cu_chunk_seq_lens: (nchunks+1,)
        causal: if True, then out[i, j] for i > j will be arbitrary, only out[i, j] for i <= j are
            guaranteed to be correct.
    Return:
        out: (nchunks, ngroups, chunk_size, chunk_size)
    """
    seqlen, ngroups, k = a.shape
    assert b.shape == a.shape
    if a.stride(-1) != 1 and a.stride(0) != 1:
        a = a.contiguous()
    if b.stride(-1) != 1 and b.stride(0) != 1:
        b = b.contiguous()

    nchunks = len(cu_chunk_seqlens) - 1
    # Allocates output.
    out_dtype = a.dtype if output_dtype is None else output_dtype
    out = torch.empty(
        (nchunks, ngroups, chunk_size, chunk_size), device=a.device, dtype=out_dtype
    )
    dot_dtype = (
        tl.bfloat16
        if a.dtype == torch.bfloat16 or b.dtype == torch.bfloat16
        else (
            tl.float16
            if a.dtype == torch.float16 or b.dtype == torch.float16
            else tl.float32
        )
    )
    grid = lambda META: (
        triton.cdiv(chunk_size, META["BLOCK_SIZE_M"])
        * triton.cdiv(chunk_size, META["BLOCK_SIZE_N"]),
        nchunks * ngroups,
    )
    with torch.accelerator.device_index(a.device.index):
        _bmm_chunk_fwd_kernel[grid](
            a_ptr=a,
            b_ptr=b,
            out_ptr=out,
            cu_chunk_seqlens_ptr=cu_chunk_seqlens,
            seqlen=seqlen,
            chunk_size=chunk_size,
            K=k,
            ngroups=ngroups,
            stride_a_seqlen=a.stride(0),
            stride_a_head=a.stride(1),
            stride_ak=a.stride(2),
            stride_b_seqlen=b.stride(0),
            stride_b_head=b.stride(1),
            stride_bk=b.stride(2),
            stride_out_chunk=out.stride(0),
            stride_out_head=out.stride(1),
            stride_outm=out.stride(-2),
            stride_outn=out.stride(-1),
            IS_CAUSAL=causal,
            dot_dtype=dot_dtype,
        )
    return out