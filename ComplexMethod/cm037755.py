def selective_scan_fn(
    u,
    ssm_states,
    delta,
    A,
    B,
    C,
    D=None,
    z=None,
    delta_bias=None,
    delta_softplus=False,
    query_start_loc=None,
    cache_indices=None,
    has_initial_state=None,
    null_block_id=NULL_BLOCK_ID,
    block_size=1024,
    block_idx_first_scheduled_token=None,
    block_idx_last_scheduled_token=None,
    initial_state_idx=None,
    cu_chunk_seqlen=None,
    last_chunk_indices=None,
) -> torch.Tensor:
    """
    u: (dim, total_length) for varlen or (batch, dim, seqlen)
        applies changes in place.
    ssm_states: (batch, dim, dstate) or (batch, nheads, dim, dstate)
        applies changes in place.
    delta: (dim, total_length) for varlen or (batch, dim, seqlen)
    A: (dim, dstate)
    B: (ngroups, dstate, total_length) for varlen or
                                        (batch,ngroups,dstate,seqlen)
    C: (ngroups, dstate, total_length) for varlen or
                                        (batch,ngroups,dstate,seqlen)
    D: (dim,)
    z: (dim, total_length) for varlen or (batch, dim, seqlen)
    dt_bias: (dim,) or (dim)
    query_start_loc: (batch + 1) int32
        The cumulative sequence lengths of the sequences in
        the batch, used to index into sequence. prepended with 0.
        for example: query_start_loc = torch.Tensor([0,10,16,17]),
        x.shape=(dim,17)
    cache_indices: (batch) int32
        A tensor with each cell is a correspondent
        input and output ssm_state indices
      - Without APC: (batch,) - single state index per batch item
      - With APC: (batch, max_positions) - cache block indices for read/write
        Each non-zero value indicates a cache block to load from and/or write to.
    has_initial_state: (batch) bool
        A tensor populated with ones and zeros,
        indicate if the ssm_state at the corresponding index should be
        used as initial state. Not providing argument assumes
        there's no initial state
    null_block_id: int
        if cache_indices is passed, lets the kernel identify padding entries
        that will not be processed,
        for example: cache_indices = [null_block_id, 1 ,20 ,null_block_id]
        in this case, the kernel will not process entries at indices 0 and 3
    block_size: int
        The block size to align the cached states to
    block_idx_first_scheduled_token: (batch,), dtype int32
        The pointer into cache_indices, where the first
        cache block to be filled is located.
    block_idx_last_scheduled_token: (batch,), dtype int32
        The pointer into cache_indices, where the last cache block
        to be filled is located.
    initial_state_idx: (batch,), dtype int32
        The pointer into cache_indices, where the cache block
        containing the initial state is located.
    returns
        output: (dim, total_length) for varlen or (batch, dim, seqlen)
                supports inplace replacement
    """
    if u.stride(-1) != 1:
        u = u.contiguous()
    if delta.stride(-1) != 1:
        delta = delta.contiguous()
    if D is not None:
        D = D.contiguous()
    if B.stride(-1) != 1:
        B = B.contiguous()
    if C.stride(-1) != 1:
        C = C.contiguous()
    if z is not None and z.stride(-1) != 1:
        z = z.contiguous()
    if B.dim() == 3 and query_start_loc is None:
        B = B.unsqueeze(1)
    if B.dim() == 2 and query_start_loc is not None:
        B = B.unsqueeze(0)
    if C.dim() == 3 and query_start_loc is None:
        C = C.unsqueeze(1)
    if C.dim() == 2 and query_start_loc is not None:
        C = C.unsqueeze(0)

    ops.selective_scan_fwd(
        u,
        delta,
        A,
        B,
        C,
        D,
        z,
        delta_bias,
        delta_softplus,
        query_start_loc,
        cache_indices,
        has_initial_state,
        ssm_states,
        null_block_id,
        block_size,
        block_idx_first_scheduled_token,
        block_idx_last_scheduled_token,
        initial_state_idx,
        cu_chunk_seqlen,
        last_chunk_indices,
    )

    if z is None:
        return delta  # output written inplace to delta
    else:
        return z