def _select_sdp_backend(query, key, value, attn_mask, dropout, is_causal, enable_gqa):
    if (
        not flash_sdp_enabled()
        and not mem_efficient_sdp_enabled()
        and not math_sdp_enabled()
        and not cudnn_sdp_enabled()
    ):
        return SDPBackend.ERROR

    ordering = (
        SDPBackend.FLASH_ATTENTION,
        SDPBackend.EFFICIENT_ATTENTION,
        SDPBackend.MATH,
        SDPBackend.CUDNN_ATTENTION,
    )

    params = SDPAParams(query, key, value, attn_mask, dropout, is_causal, enable_gqa)

    for backend in ordering:
        if backend == SDPBackend.CUDNN_ATTENTION:
            if can_use_cudnn_attention(params):
                return SDPBackend.CUDNN_ATTENTION
        if backend == SDPBackend.FLASH_ATTENTION:
            if can_use_flash_attention(params) and _can_use_flash_sdpa_jagged(params):
                return SDPBackend.FLASH_ATTENTION
        if backend == SDPBackend.EFFICIENT_ATTENTION:
            if can_use_efficient_attention(params) and _can_use_efficient_sdpa_jagged(
                params
            ):
                return SDPBackend.EFFICIENT_ATTENTION
        if backend == SDPBackend.MATH:
            if math_sdp_enabled() and _can_use_math_sdpa_jagged(params):
                return SDPBackend.MATH

    log.warning("Memory efficient kernel not used because:")
    can_use_efficient_attention(params, debug=True)
    _can_use_efficient_sdpa_jagged(params, debug=True)
    log.warning("Flash attention kernel not used because:")
    can_use_flash_attention(params, debug=True)
    _can_use_flash_sdpa_jagged(params, debug=True)
    log.warning("Math attention kernel not used because:")
    _can_use_math_sdpa_jagged(params, debug=True)
    log.warning("cuDNN attention kernel not used because:")
    can_use_cudnn_attention(params, debug=True)
    return SDPBackend.ERROR