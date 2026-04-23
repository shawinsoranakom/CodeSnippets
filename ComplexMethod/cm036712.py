def selective_scan_opcheck_fn(
    u,
    delta,
    A,
    B,
    C,
    D=None,
    z=None,
    delta_bias=None,
    delta_softplus=False,
    cu_seq_len=None,
    cache_indices=None,
    has_initial_state=None,
    ssm_states=None,
    null_block_id=NULL_BLOCK_ID,
    block_size=2048,
    block_idx_first_scheduled_token=None,
    block_idx_last_scheduled_token=None,
    initial_state_idx=None,
    cu_chunk_seqlen=None,
    last_chunk_indices=None,
):
    """if return_last_state is True, returns (out, last_state)
    last_state has shape (batch, dim, dstate).
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
    if B.dim() == 3 and cu_seq_len is None:
        B = B.unsqueeze(1)
    if B.dim() == 2 and cu_seq_len is not None:
        B = B.unsqueeze(0)
    if C.dim() == 3 and cu_seq_len is None:
        C = C.unsqueeze(1)
    if C.dim() == 2 and cu_seq_len is not None:
        C = C.unsqueeze(0)

    # Disable test_autograd_registration for now as it seems to trigger
    # a bogus error.
    opcheck(
        torch.ops._C.selective_scan_fwd,
        (
            u,
            delta,
            A,
            B,
            C,
            D,
            z,
            delta_bias,
            delta_softplus,
            cu_seq_len,
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
        ),
        test_utils=["test_schema", "test_faketensor"],
    )