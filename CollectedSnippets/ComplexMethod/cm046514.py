def _drive(
    n_ctx,
    model_gib,
    gpus,
    native_ctx = 131072,
    kv_per_token_bytes = 325_000,
    can_estimate_kv = True,
):
    """Drive the post-metadata portion of load_model with stubbed inputs.

    Mirrors the decision block at llama_cpp.py:1137-1296 so we can assert
    the command that would be built, without subprocesses or GPU probes.
    """
    inst = _make_backend(native_ctx = native_ctx)
    model_size = int(model_gib * GIB)
    cache_type_kv = None

    def fake_estimate(n_ctx_, _type = None):
        return 0 if n_ctx_ <= 0 else n_ctx_ * kv_per_token_bytes

    inst._estimate_kv_cache_bytes = fake_estimate
    inst._can_estimate_kv = lambda: can_estimate_kv

    context_length = inst._context_length

    effective_ctx = n_ctx if n_ctx > 0 else (context_length or 0)
    max_available_ctx = context_length or effective_ctx
    if n_ctx > 0:
        effective_ctx = n_ctx
    elif context_length is not None:
        effective_ctx = context_length
    else:
        effective_ctx = 0
    original_ctx = effective_ctx
    max_available_ctx = context_length or effective_ctx

    gpu_indices, use_fit = None, True
    explicit_ctx = n_ctx > 0

    if gpus and inst._can_estimate_kv() and effective_ctx > 0:
        native_ctx_for_cap = context_length or effective_ctx
        if native_ctx_for_cap > 0:
            ranked_for_cap = sorted(gpus, key = lambda g: g[1], reverse = True)
            best_cap = 0
            for n_gpus in range(1, len(ranked_for_cap) + 1):
                subset = ranked_for_cap[:n_gpus]
                pool_mib = sum(free for _, free in subset)
                capped = inst._fit_context_to_vram(
                    native_ctx_for_cap,
                    pool_mib,
                    model_size,
                    cache_type_kv,
                )
                kv = inst._estimate_kv_cache_bytes(capped, cache_type_kv)
                total_mib = (model_size + kv) / (1024 * 1024)
                if total_mib <= pool_mib * 0.90:
                    best_cap = max(best_cap, capped)
            if best_cap > 0:
                max_available_ctx = best_cap

        if explicit_ctx:
            requested_total = model_size + inst._estimate_kv_cache_bytes(
                effective_ctx, cache_type_kv
            )
            gpu_indices, use_fit = inst._select_gpus(requested_total, gpus)
        else:
            ranked = sorted(gpus, key = lambda g: g[1], reverse = True)
            matched = False
            for n_gpus in range(1, len(ranked) + 1):
                subset = ranked[:n_gpus]
                pool_mib = sum(free for _, free in subset)
                capped = inst._fit_context_to_vram(
                    effective_ctx,
                    pool_mib,
                    model_size,
                    cache_type_kv,
                )
                kv = inst._estimate_kv_cache_bytes(capped, cache_type_kv)
                total_mib = (model_size + kv) / (1024 * 1024)
                if total_mib <= pool_mib * 0.90:
                    effective_ctx = capped
                    gpu_indices = sorted(idx for idx, _ in subset)
                    use_fit = False
                    matched = True
                    break
            if not matched:
                effective_ctx = min(FALLBACK_CTX, effective_ctx)
    elif gpus:
        gpu_indices, use_fit = inst._select_gpus(model_size, gpus)
        if use_fit and not explicit_ctx:
            effective_ctx = (
                min(FALLBACK_CTX, effective_ctx) if effective_ctx > 0 else FALLBACK_CTX
            )

    return {
        "c_arg": effective_ctx if effective_ctx > 0 else 0,
        "use_fit": use_fit,
        "gpu_indices": gpu_indices,
        "max_available_ctx": max_available_ctx,
        "original_ctx": original_ctx,
    }