def run_large_context_topk_test(
    batch_size: int,
    seq_lens: list[int],
    top_k: int,
    data_type: str = "random",
    seed: int = 42,
) -> None:
    """
    Helper to run persistent_topk kernel test with given parameters.

    Args:
        batch_size: Number of rows/sequences
        seq_lens: List of sequence lengths (one per row)
        top_k: Number of top elements to select
        data_type: Type of test data to generate
        seed: Random seed for reproducibility
    """
    torch.set_default_device("cuda:0")
    set_random_seed(seed)

    # Create test data
    num_rows = batch_size
    max_len = max(seq_lens)
    lengths = torch.tensor(seq_lens, dtype=torch.int32, device="cuda")

    if data_type == "random":
        logits = torch.randn(num_rows, max_len, dtype=torch.float32, device="cuda")
    elif data_type == "sorted_asc":
        # Each row gets its own ascending sequence based on its length
        logits = torch.empty(num_rows, max_len, dtype=torch.float32, device="cuda")
        for i, length in enumerate(seq_lens):
            logits[i, :length] = torch.arange(
                length, dtype=torch.float32, device="cuda"
            )
            if length < max_len:
                logits[i, length:] = float("-inf")
    elif data_type == "sorted_desc":
        # Each row gets its own descending sequence based on its length
        logits = torch.empty(num_rows, max_len, dtype=torch.float32, device="cuda")
        for i, length in enumerate(seq_lens):
            logits[i, :length] = torch.arange(
                length, 0, -1, dtype=torch.float32, device="cuda"
            )
            if length < max_len:
                logits[i, length:] = float("-inf")
    elif data_type == "all_same":
        logits = torch.ones(num_rows, max_len, dtype=torch.float32, device="cuda")
        for i, length in enumerate(seq_lens):
            if length < max_len:
                logits[i, length:] = float("-inf")
    elif data_type == "many_ties":
        # Only 10 unique values, many duplicates
        logits = torch.randint(0, 10, (num_rows, max_len), device="cuda").float() / 10.0
        for i, length in enumerate(seq_lens):
            if length < max_len:
                logits[i, length:] = float("-inf")
    elif data_type == "small_differences":
        # Very small differences to test float precision
        base = torch.randn(num_rows, max_len, dtype=torch.float32, device="cuda")
        noise = (
            torch.randn(num_rows, max_len, dtype=torch.float32, device="cuda") * 1e-6
        )
        logits = base + noise
        for i, length in enumerate(seq_lens):
            if length < max_len:
                logits[i, length:] = float("-inf")
    else:
        raise ValueError(f"Unknown data_type: {data_type}")

    # Create output tensor
    indices = torch.empty((num_rows, top_k), dtype=torch.int32, device="cuda")

    workspace = torch.empty(1024 * 1024, dtype=torch.uint8, device="cuda")
    max_seq_len = max(seq_lens)
    torch.ops._C.persistent_topk(
        logits, lengths, indices, workspace, top_k, max_seq_len
    )

    torch.accelerator.synchronize()

    torch_indices = torch.empty((num_rows, top_k), dtype=torch.int32, device="cuda")
    for i in range(num_rows):
        length = seq_lens[i]
        k_i = min(top_k, length)
        if k_i > 0:
            idx = logits[i, :length].topk(k_i, dim=-1)[1]
            torch_indices[i, :k_i] = idx
            if k_i < top_k:
                torch_indices[i, k_i:] = -1
        else:
            torch_indices[i, :] = -1

    # Compare results
    for i in range(num_rows):
        length = seq_lens[i]
        k_i = min(top_k, length)

        if k_i == 0:
            continue

        cuda_row = indices[i, :k_i].cpu()
        torch_row = torch_indices[i, :k_i].cpu()

        # Filter out -1 padding values from cuda_row
        valid_mask = cuda_row >= 0
        cuda_row = cuda_row[valid_mask]

        # Compare sets (order may differ for ties)
        cuda_set = set(cuda_row.tolist())
        torch_set = set(torch_row.tolist())

        if cuda_set == torch_set:
            continue

        # If sets differ, check if it's due to equal values (ties)
        cuda_vals = logits[i, cuda_row].cpu()
        torch_vals = logits[i, torch_row].cpu()

        # Check that min CUDA value >= max of values NOT in top-k
        if k_i < length:
            non_topk_indices = torch.tensor(
                list(set(range(length)) - cuda_set), dtype=torch.int32
            )
            if len(non_topk_indices) > 0:
                non_topk_vals = logits[i, non_topk_indices].cpu()
                min_cuda_val = cuda_vals.min()
                max_non_topk = non_topk_vals.max()

                # Allow small tolerance for floating point errors
                assert min_cuda_val >= max_non_topk - 1e-4, (
                    f"Row {i}: CUDA top-k contains values smaller than non-top-k. "
                    f"Min CUDA: {min_cuda_val}, Max non-top-k: {max_non_topk}, "
                    f"Length: {length}, k: {k_i}, CUDA indices: {sorted(cuda_set)[:10]}..., "  # noqa: E501
                    f"Expected indices: {sorted(torch_set)[:10]}..."
                )

        # For ties, verify the values are close
        assert torch.allclose(
            cuda_vals.sort(descending=True)[0],
            torch_vals.sort(descending=True)[0],
            rtol=1e-4,
            atol=1e-4,
        ), f"""Row {i}: Top-k values don't match.
            CUDA: {cuda_vals.sort(descending=True)[0][:10]},
            Torch: {torch_vals.sort(descending=True)[0][:10]}"""