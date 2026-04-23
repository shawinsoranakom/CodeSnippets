def _build_test_case(seq_lens, block_size, seed=42):
    """Build a synthetic FP8 cache and compute the expected BF16 output.

    This simulates what concat_and_cache_ds_mla_kernel writes into the
    KV cache, then computes what cp_gather_and_upconvert should produce.

    Args:
        seq_lens: List of sequence lengths, one per request.
        block_size: Number of tokens per physical cache block.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (cache, block_table, seq_lens_t, workspace_starts_t,
                  num_reqs, total_tokens, expected_output).
    """
    torch.manual_seed(seed)

    num_reqs = len(seq_lens)
    total_tokens = sum(seq_lens)

    # workspace_starts[r] = sum of seq_lens[0..r-1]
    # This tells the kernel where in the output buffer each request's
    # gathered tokens should be written.
    workspace_starts = []
    s = 0
    for sl in seq_lens:
        workspace_starts.append(s)
        s += sl

    # How many physical cache blocks each request needs
    blocks_per_req = [math.ceil(s / block_size) for s in seq_lens]
    total_blocks = sum(blocks_per_req)
    max_blocks = max(blocks_per_req)

    # Block table maps (request, logical_block_idx) -> physical_block_id.
    # Here we assign blocks contiguously: request 0 gets blocks [0, 1, ...],
    # request 1 gets the next set, etc.
    block_table = torch.zeros(num_reqs, max_blocks, dtype=torch.int32, device="cuda")
    block_idx = 0
    for r in range(num_reqs):
        for b in range(blocks_per_req[r]):
            block_table[r, b] = block_idx
            block_idx += 1

    # The raw paged cache: [num_blocks, block_size, 656] as uint8
    cache = torch.zeros(
        total_blocks, block_size, ENTRY_BYTES, dtype=torch.uint8, device="cuda"
    )
    # Expected kernel output: [total_tokens, 576] as BF16
    expected = torch.zeros(
        total_tokens, NOPE_DIM + ROPE_DIM, dtype=torch.bfloat16, device="cuda"
    )

    # Fill each token's cache entry and compute expected output
    for r in range(num_reqs):
        for t in range(seq_lens[r]):
            out_idx = workspace_starts[r] + t
            # Map token position -> (physical_block, offset_within_block)
            phys = block_table[r, t // block_size].item()
            off = t % block_size

            # --- NoPE section: 4 tiles of 128 FP8 values, each with a scale ---
            for tile in range(NUM_TILES):
                start = tile * GROUP_SIZE

                # Generate random data and quantize to FP8 e4m3
                fp8_vals = torch.randn(GROUP_SIZE, device="cuda").to(
                    torch.float8_e4m3fn
                )
                # Pack FP8 bytes into cache at bytes [start : start+128]
                cache[phys, off, start : start + GROUP_SIZE] = fp8_vals.view(
                    torch.uint8
                )

                # Random positive scale in [0.1, 2.1]
                scale = (torch.rand(1, device="cuda") * 2.0 + 0.1).item()
                scale_t = torch.tensor([scale], dtype=torch.float32, device="cuda")
                # Pack scale as 4 raw bytes at bytes [512 + tile*4 : ...]
                cache[phys, off, NOPE_DIM + tile * 4 : NOPE_DIM + (tile + 1) * 4] = (
                    scale_t.view(torch.uint8)
                )

                # Reference dequant: fp8 -> float32, multiply scale, -> bf16.
                # This matches the CUDA path: fp8 -> half -> float * scale -> bf16.
                # (fp8 -> half is exact, half -> float is exact, so fp8 -> float
                # gives the same result regardless of intermediate type.)
                expected[out_idx, start : start + GROUP_SIZE] = (
                    fp8_vals.float() * scale
                ).bfloat16()

            # --- RoPE section: 64 BF16 values, direct copy (no dequant) ---
            rope = torch.randn(ROPE_DIM, dtype=torch.bfloat16, device="cuda")
            # Pack RoPE bytes into cache at bytes [528 : 656]
            cache[phys, off, NOPE_DIM + 16 :] = rope.view(torch.uint8)
            # Expected output: exact copy
            expected[out_idx, NOPE_DIM:] = rope

    seq_lens_t = torch.tensor(seq_lens, dtype=torch.int32, device="cuda")
    workspace_starts_t = torch.tensor(
        workspace_starts, dtype=torch.int32, device="cuda"
    )

    return (
        cache,
        block_table,
        seq_lens_t,
        workspace_starts_t,
        num_reqs,
        total_tokens,
        expected,
    )