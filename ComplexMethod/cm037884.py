def verify_and_update_config(cls, vllm_config: "VllmConfig") -> None:
        """
        Enable FULL_AND_PIECEWISE cuda graph mode by default (required
        to get good performance for mamba layers in V1).

        Args:
            vllm_config: vLLM Config
        """
        model_config = vllm_config.model_config
        cache_config = vllm_config.cache_config

        if cache_config.enable_prefix_caching:
            if cache_config.mamba_cache_mode == "none":
                if (
                    model_config.supports_mamba_prefix_caching
                    and vllm_config.speculative_config is not None
                ):
                    cache_config.mamba_cache_mode = "align"
                    logger.warning(
                        "Mamba cache mode is set to 'align' for %s by default "
                        "when prefix caching and speculative decoding are enabled",
                        model_config.architecture,
                    )
                else:
                    cache_config.mamba_cache_mode = (
                        "all" if model_config.supports_mamba_prefix_caching else "align"
                    )
                    logger.warning(
                        "Mamba cache mode is set to '%s' for %s by default "
                        "when prefix caching is enabled",
                        cache_config.mamba_cache_mode,
                        model_config.architecture,
                    )
            if (
                cache_config.mamba_cache_mode == "all"
                and not model_config.supports_mamba_prefix_caching
            ):
                cache_config.mamba_cache_mode = "align"
                logger.warning(
                    "Hybrid or mamba-based model detected without support "
                    "for prefix caching with Mamba cache 'all' mode: "
                    "falling back to 'align' mode."
                )
            if cache_config.mamba_cache_mode == "align":
                assert vllm_config.scheduler_config.enable_chunked_prefill, (
                    "Chunked prefill is required for mamba cache mode 'align'."
                )
            logger.info(
                "Warning: Prefix caching in Mamba cache '%s' "
                "mode is currently enabled. "
                "Its support for Mamba layers is experimental. "
                "Please report any issues you may observe.",
                cache_config.mamba_cache_mode,
            )
            # By default, mamba block size will be set to max_model_len (see
            # below). When enabling prefix caching, we align mamba block size
            # to the block size as the basic granularity for prefix caching.
            if cache_config.mamba_block_size is None:
                cache_config.mamba_block_size = cache_config.block_size
        else:
            if cache_config.mamba_cache_mode != "none":
                cache_config.mamba_cache_mode = "none"
                logger.warning(
                    "Mamba cache mode is set to 'none' when prefix caching is disabled"
                )
            if cache_config.mamba_block_size is None:
                cache_config.mamba_block_size = model_config.max_model_len