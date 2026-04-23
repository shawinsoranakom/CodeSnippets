def _count_warmup_iterations(model: torch.nn.Module, max_tokens: int) -> int:
    seen_fp8_sizes: set[torch.Size] = set(FP8_GEMM_NT_WARMUP_CACHE)
    seen_grouped_sizes: set[torch.Size] = set(
        GROUPED_FP8_GEMM_NT_CONTIGUOUS_WARMUP_CACHE
    )

    total = 0
    for m in model.modules():
        if _fp8_linear_may_use_deep_gemm(m):
            w, _, _ = _extract_data_from_linear_base_module(m)
            if w.size() not in seen_fp8_sizes:
                total += len(_get_fp8_gemm_nt_m_values(w, max_tokens))
                seen_fp8_sizes.add(w.size())
        elif _fused_moe_grouped_gemm_may_use_deep_gemm(m):
            w13, _, w2, _, num_topk = _extract_data_from_fused_moe_module(m)
            if w13.size() in seen_grouped_sizes and w2.size() in seen_grouped_sizes:
                continue
            MAX_M, block_m, _ = _get_grouped_gemm_params(w13, w2, num_topk, max_tokens)
            n_values = (MAX_M - block_m) // block_m + 1
            if w13.size() not in seen_grouped_sizes:
                total += n_values
                seen_grouped_sizes.add(w13.size())
            if w2.size() not in seen_grouped_sizes:
                total += n_values
                seen_grouped_sizes.add(w2.size())
    return total