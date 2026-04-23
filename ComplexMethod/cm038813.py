def use_trtllm_attention(
    num_qo_heads: int,
    num_kv_heads: int,
    num_tokens: int,
    max_seq_len: int,
    dcp_world_size: int,
    kv_cache_dtype: str,
    q_dtype: torch.dtype,
    is_prefill: bool,
    # None means auto-detection, True means force on, False means force off
    force_use_trtllm: bool | None = None,
    has_sinks: bool = False,
    has_spec: bool = False,
) -> bool:
    """Return `True` if TRTLLM attention is used."""

    # CLI argument is set to 0 - respect it
    if force_use_trtllm is not None and not force_use_trtllm:
        return False

    # Decode context parallel is not supported
    if dcp_world_size > 1:
        logger.warning_once(
            "Trtllm does not support returning LSE and as a result "
            "does not support DCP, reverting to FlashInfer"
        )
        return False

    # The platform is not supported
    if not supports_trtllm_attention():
        if force_use_trtllm:
            logger.warning_once(
                "TRTLLM attention is not supported on this platform, "
                "but --attention-config.use_trtllm_attention is set to 1"
            )
        return False

    # The combination of query and key heads is not supported
    if num_qo_heads % num_kv_heads != 0:
        if force_use_trtllm:
            logger.warning_once(
                "TRTLLM attention is not supported for this combination of "
                "query and key heads, but --attention-config.use_trtllm_attention is "
                "set to 1"
            )
        return False

    if has_spec and not is_prefill:
        # Speculative decoding requires TRTLLM attention for decodes
        logger.info_once("Using TRTLLM attention (enabled for speculative decoding).")
        return True

    # Must use TRTLLM attention if query is FP8 quantized
    if q_dtype == current_platform.fp8_dtype():
        logger.info_once("Using TRTLLM attention (query is quantized).")
        return True

    # If sinks are being used, we must use TRTLLM attention as it's
    # the only backend that supports them
    if has_sinks:
        logger.info_once("Using TRTLLM attention (required for attention sinks).")
        return True

    if force_use_trtllm is None:
        # CLI argument not set - use auto-detection
        if is_prefill:
            # Prefill auto-detection
            use_trtllm = kv_cache_dtype == "auto"
            if use_trtllm:
                logger.warning_once("Using TRTLLM prefill attention (auto-detected).")
        else:
            # Decode auto-detection
            use_trtllm = num_tokens <= 256 and kv_cache_dtype == "auto"
            if use_trtllm:
                logger.warning_once("Using TRTLLM decode attention (auto-detected).")
        return use_trtllm

    # CLI argument is set to 1 - respect it
    logger.info_once(
        "Using TRTLLM attention (--attention-config.use_trtllm_attention is set to 1)"
    )
    return True