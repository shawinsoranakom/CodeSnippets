def _build_attention_metadata(
    requests: list,
    block_size: int,
    device: torch.device,
    builder_instance,
) -> tuple:
    """
    Build attention metadata from batch requests.

    Args:
        requests: List of BatchRequest objects
        block_size: KV cache block size
        device: Target device
        builder_instance: Metadata builder instance

    Returns:
        Tuple of (metadata, kv_cache_num_blocks)
    """
    q_lens = [r.q_len for r in requests]
    kv_lens = [r.kv_len for r in requests]
    total_q = sum(q_lens)
    max_kv = max(kv_lens)

    # Build query start locations
    q_start_cpu = torch.tensor(
        [0] + [sum(q_lens[: i + 1]) for i in range(len(q_lens))],
        dtype=torch.int32,
    )
    q_start_gpu = q_start_cpu.to(device)

    # Build sequence lengths
    seq_lens_cpu = torch.tensor(kv_lens, dtype=torch.int32)
    seq_lens_gpu = seq_lens_cpu.to(device)

    # Build num_computed_tokens (context length for each request)
    context_lens = [kv_len - q_len for q_len, kv_len in zip(q_lens, kv_lens)]
    num_computed_tokens_cpu = torch.tensor(context_lens, dtype=torch.int32)

    # Build block table
    num_blocks_per_req = [(kv + block_size - 1) // block_size for kv in kv_lens]
    max_num_blocks = max(num_blocks_per_req)

    block_table_cpu = np.zeros((len(requests), max_num_blocks), dtype=np.int32)
    current_block = 0
    for i, num_blocks in enumerate(num_blocks_per_req):
        for j in range(num_blocks):
            block_table_cpu[i, j] = current_block
            current_block += 1

    block_table_gpu = torch.from_numpy(block_table_cpu).to(device)

    # Build slot mapping
    slot_mapping_list = []
    for i, (q_len, kv_len, num_blocks) in enumerate(
        zip(q_lens, kv_lens, num_blocks_per_req)
    ):
        context_len = kv_len - q_len
        for j in range(q_len):
            token_kv_idx = context_len + j
            block_idx = token_kv_idx // block_size
            offset_in_block = token_kv_idx % block_size
            global_block_id = block_table_cpu[i, block_idx]
            slot_id = global_block_id * block_size + offset_in_block
            slot_mapping_list.append(slot_id)

    slot_mapping = torch.tensor(slot_mapping_list, dtype=torch.int64, device=device)

    # Create CommonAttentionMetadata
    from vllm.v1.attention.backends.utils import CommonAttentionMetadata

    common_attn_metadata = CommonAttentionMetadata(
        num_reqs=len(requests),
        max_query_len=max(q_lens),
        max_seq_len=max_kv,
        num_actual_tokens=total_q,
        query_start_loc=q_start_gpu,
        query_start_loc_cpu=q_start_cpu,
        seq_lens=seq_lens_gpu,
        _seq_lens_cpu=seq_lens_cpu,
        _num_computed_tokens_cpu=num_computed_tokens_cpu,
        slot_mapping=slot_mapping,
        block_table_tensor=block_table_gpu,
        dcp_local_seq_lens=None,
    )

    # Use the production build() method
    metadata = builder_instance.build(
        common_prefix_len=0,
        common_attn_metadata=common_attn_metadata,
        fast_build=False,
    )

    return metadata, current_block