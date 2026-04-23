def create_and_prepopulate_kv_cache(
    kv_c_contexts: list[torch.Tensor],
    k_pe_contexts: list[torch.Tensor],
    block_size: int,
    head_size: int,
    dtype: torch.dtype,
    device: torch.device,
    num_blocks: int,
    common_attn_metadata: CommonAttentionMetadata,
    randomize_blocks: bool = True,
    kv_cache_dtype: str | None = None,
    scale: float | torch.Tensor = 1.0,
) -> torch.Tensor:
    """Create and prepopulate an MLA KV cache with context data.

    Args:
        kv_c_contexts: List of latent KV context tensors for each sequence
        k_pe_contexts: List of key positional embedding context tensors
                       for each sequence
        block_size: Size of each block
        head_size: Size of each head (latent dimension)
        dtype: Data type for the cache
        device: Device to create the cache on
        num_blocks: Total number of blocks in the cache
        common_attn_metadata: Common attention metadata
        randomize_blocks: Whether to randomly permute blocks
                          or use sequential order
        kv_cache_dtype: Optional kv cache dtype string. For fp8 cache dtype,
                        the cache is populated via concat_and_cache_mla.
        scale: Scaling factor forwarded to concat_and_cache_mla when the
               fp8 cache layout is requested.

    Returns:
        MLA KV cache tensor
    """
    batch_size = len(kv_c_contexts)
    seq_lens = common_attn_metadata.seq_lens.cpu()
    query_lens = (
        common_attn_metadata.query_start_loc_cpu[1:]
        - common_attn_metadata.query_start_loc_cpu[:-1]
    )
    context_lens = seq_lens - query_lens
    block_table = common_attn_metadata.block_table_tensor
    slot_mapping = common_attn_metadata.slot_mapping

    fp8_attention = kv_cache_dtype and kv_cache_dtype.startswith("fp8")
    use_fp8_ds_mla = kv_cache_dtype == "fp8_ds_mla"

    if fp8_attention:
        if use_fp8_ds_mla:
            kv_lora_rank = kv_c_contexts[0].shape[-1]
            rope_dim = k_pe_contexts[0].shape[-1]
            # 4 * 4: 4 float32 scale values for 128-element tiles
            # 2 * rope_dim: 16-bit RoPE values
            kv_entry_size = kv_lora_rank + 4 * 4 + 2 * rope_dim
        else:
            kv_entry_size = head_size

        kv_cache = torch.zeros(
            num_blocks, block_size, kv_entry_size, dtype=torch.uint8, device=device
        )
        scale_tensor = (
            scale
            if isinstance(scale, torch.Tensor)
            else torch.tensor(scale, dtype=torch.float32, device=device)
        )
        scale_tensor = scale_tensor.to(device=device, dtype=torch.float32)
    else:
        # Create MLA KV cache: (num_blocks, block_size, head_size)
        kv_cache = torch.zeros(
            num_blocks, block_size, head_size, dtype=dtype, device=device
        )
        kv_cache_flat = kv_cache.view(-1, head_size)

    # Populate the cache with the context tokens
    # Start from block_id=1 since block_id=0 is considered the null block
    start_block_idx = 1
    for i in range(batch_size):
        kv_c_context, k_pe_context = kv_c_contexts[i], k_pe_contexts[i]
        context_len = kv_c_context.shape[0]
        if context_len == 0:
            start_block_idx += cdiv(int(seq_lens[i]), block_size)
            continue

        start = start_block_idx * block_size

        if fp8_attention:
            slots = torch.arange(context_len, device=device, dtype=torch.long) + start
            ops.concat_and_cache_mla(
                kv_c_context,
                k_pe_context.squeeze(1),
                kv_cache,
                slots,
                kv_cache_dtype=kv_cache_dtype,
                scale=scale_tensor,
            )
        else:
            kv_context = torch.cat([kv_c_context, k_pe_context.squeeze(1)], dim=-1)
            end = start + kv_context.shape[0]
            kv_cache_flat[start:end, ...] = kv_context

        # Stay block aligned and allocate enough blocks for the new tokens
        start_block_idx += cdiv(int(seq_lens[i]), block_size)

    blocks_end = start_block_idx

    # Permute the context blocks (excluding block 0 which is null)
    if randomize_blocks:
        perm = (
            torch.randperm(blocks_end - 1) + 1
        )  # Random permutation starting from block 1
    else:
        perm = torch.arange(1, blocks_end)  # Sequential order starting from block 1

    inv_perm = torch.zeros(blocks_end, dtype=torch.long, device=device)
    inv_perm[1:] = torch.argsort(perm) + 1  # Add 1 to account for starting from block 1
    kv_cache[1:blocks_end, ...] = kv_cache[perm, ...]

    # Construct the right block table
    # Start from block_id=1 since block_id=0 is considered the null block
    start_block_idx = 1
    for i in range(batch_size):
        num_blocks_for_seq = cdiv(int(seq_lens[i]), block_size)
        start = start_block_idx
        end = start + num_blocks_for_seq
        block_table[i, :num_blocks_for_seq] = inv_perm[start:end]
        block_table[i, num_blocks_for_seq:] = 0
        start_block_idx += num_blocks_for_seq

        # Create a realistic slot mapping that corresponds to the block table
    for i in range(batch_size):
        token_offsets = torch.arange(int(query_lens[i])) + int(context_lens[i])
        block_indices = token_offsets // block_size
        token_inter_block_offsets = token_offsets % block_size
        start = common_attn_metadata.query_start_loc_cpu[i]
        end = common_attn_metadata.query_start_loc_cpu[i + 1]
        slot_mapping[start:end] = block_table[
            i, block_indices
        ] * block_size + token_inter_block_offsets.to(device)

    return kv_cache