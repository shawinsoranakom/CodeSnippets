def flashinfer_wrapper(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    scale: float,
    workspace_buffer: torch.Tensor,
    cu_seqlens: torch.Tensor | None = None,
    max_seqlen: torch.Tensor | None = None,
    sequence_lengths: torch.Tensor | None = None,
) -> torch.Tensor:
    from flashinfer.prefill import cudnn_batch_prefill_with_kv_cache

    is_reshaped = q.dim() == 4

    if is_reshaped:
        reshape_batch_size = q.shape[0]
        q, k, v = (einops.rearrange(x, "b s ... -> (b s) ...") for x in [q, k, v])
    # cuDNN <= 9.10.2.21 requires q, k to be contiguous
    # this comes with no cost for ViTs with RoPE because
    # RoPE has already made q and k contiguous.
    q, k = q.contiguous(), k.contiguous()

    assert cu_seqlens is not None
    assert max_seqlen is not None
    assert sequence_lengths is not None
    assert len(cu_seqlens) % 2 == 0, "cu_seqlens must be divisible by 2"
    cu_seqlength = len(cu_seqlens) // 2
    batch_offsets_qko = cu_seqlens[:cu_seqlength].view(-1, 1, 1, 1)
    batch_offsets_v = cu_seqlens[cu_seqlength:].view(-1, 1, 1, 1)
    sequence_lengths = sequence_lengths.view(-1, 1, 1, 1)
    max_seqlen = max_seqlen.item()

    output, _ = cudnn_batch_prefill_with_kv_cache(
        q,
        k,
        v,
        scale,
        workspace_buffer,
        max_token_per_sequence=max_seqlen,
        max_sequence_kv=max_seqlen,
        actual_seq_lens_q=sequence_lengths,
        actual_seq_lens_kv=sequence_lengths,
        causal=False,
        return_lse=False,
        batch_offsets_q=batch_offsets_qko,
        batch_offsets_k=batch_offsets_qko,
        batch_offsets_v=batch_offsets_v,
        batch_offsets_o=batch_offsets_qko,
    )

    if is_reshaped:
        output = einops.rearrange(output, "(b s) h d -> b s h d", b=reshape_batch_size)

    return output