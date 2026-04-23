def split_indexer_prefill_chunks(
    seq_lens_cpu: torch.Tensor,
    query_lens_cpu: torch.Tensor,
    workspace_size: int,
    max_logits_bytes: int,
    request_offset: int = 0,
) -> list[tuple[slice, slice]]:
    """
    Split prefill requests into chunks for the sparse indexer, respecting:
    - N constraint: total_seq_lens <= workspace_size (existing O(N) workspace)
    - Logits constraint: M * N * 4 <= max_logits_bytes

    When a single request-level chunk still exceeds the logits budget,
    sub-chunks on the query dimension (M) to bound peak memory.

    Returns list of (req_slice, query_slice) tuples.
    """
    chunks: list[tuple[slice, slice]] = []
    n = len(seq_lens_cpu)
    max_logits_elems = max_logits_bytes // 4
    end = 0

    while end < n:
        start, chunk_m, chunk_n = end, 0, 0

        while end < n:
            q, s = query_lens_cpu[end].item(), seq_lens_cpu[end].item()
            new_m, new_n = chunk_m + q, chunk_n + s
            if new_n <= workspace_size and new_m * new_n <= max_logits_elems:
                chunk_m, chunk_n = new_m, new_n
                end += 1
            else:
                break

        # A single request can exceed the budget, requiring sub-chunking
        # on the query dimension.
        if end == start:
            chunk_m, chunk_n = query_lens_cpu[end].item(), seq_lens_cpu[end].item()
            end += 1

        req_slice = slice(start + request_offset, end + request_offset)
        max_q = max(1, max_logits_elems // chunk_n) if chunk_n > 0 else chunk_m
        for q_off in range(0, chunk_m, max_q):
            sub_m = min(max_q, chunk_m - q_off)
            chunks.append((req_slice, slice(q_off, q_off + sub_m)))

    return chunks