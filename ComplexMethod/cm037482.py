def _align_hybrid_block_size(
        cls,
        vllm_config: "VllmConfig",
        backend_cls: "type[AttentionBackend]",
    ) -> None:
        """
        For hybrid attention/mamba models, ensure that the attention page
        size is >= the mamba page size, and pad the mamba page size to match.
        """
        from math import lcm

        from vllm.config.vllm import set_current_vllm_config
        from vllm.model_executor.models import ModelRegistry
        from vllm.utils.math_utils import cdiv
        from vllm.utils.torch_utils import STR_DTYPE_TO_TORCH_DTYPE
        from vllm.v1.attention.backend import MultipleOf
        from vllm.v1.kv_cache_interface import (
            FullAttentionSpec,
            MambaSpec,
            MLAAttentionSpec,
            get_kv_quant_mode,
        )

        cache_config = vllm_config.cache_config
        model_config = vllm_config.model_config
        parallel_config = vllm_config.parallel_config

        if cache_config.cache_dtype == "auto":
            kv_cache_dtype = model_config.dtype
        else:
            kv_cache_dtype = STR_DTYPE_TO_TORCH_DTYPE[cache_config.cache_dtype]

        kv_quant_mode = get_kv_quant_mode(cache_config.cache_dtype)

        # Compute attention page size for 1 token
        if model_config.use_mla:
            attn_page_size_1_token = MLAAttentionSpec(
                block_size=1,
                num_kv_heads=model_config.get_num_kv_heads(parallel_config),
                head_size=model_config.get_head_size(),
                dtype=kv_cache_dtype,
                kv_quant_mode=kv_quant_mode,
            ).page_size_bytes
        else:
            attn_page_size_1_token = FullAttentionSpec(
                block_size=1,
                num_kv_heads=model_config.get_num_kv_heads(parallel_config),
                head_size=model_config.get_head_size(),
                dtype=kv_cache_dtype,
                kv_quant_mode=kv_quant_mode,
            ).page_size_bytes

        # Compute mamba page size
        model_cls, _ = ModelRegistry.resolve_model_cls(
            model_config.architecture,
            model_config=model_config,
        )
        mamba_page_size = MambaSpec(
            shapes=model_cls.get_mamba_state_shape_from_config(vllm_config),
            dtypes=model_cls.get_mamba_state_dtype_from_config(vllm_config),
            block_size=-1,
        ).page_size_bytes

        if mamba_page_size == 0:
            return

        # mamba_block_size here should either be user specified value or None
        mamba_block_size = (
            cache_config.mamba_block_size
            if cache_config.user_specified_mamba_block_size
            else None
        )

        # Get kernel block alignment from the backend's supported sizes
        with set_current_vllm_config(vllm_config):
            kernel_block_alignment_size = max(
                min(
                    s.base if isinstance(s, MultipleOf) else s
                    for s in backend_cls.get_supported_kernel_block_sizes()
                ),
                cache_config.block_size,
            )

        if cache_config.mamba_cache_mode == "all":
            # With prefix caching, align to mamba chunk size for kernel perf
            # TODO(tdoublep): this constraint can be relaxed fairly
            # easily by changing the way we layout chunks in the
            # mamba2 kernels.
            base_chunk_size = mamba_block_size or model_config.get_mamba_chunk_size()
            assert base_chunk_size is not None
            attn_tokens_per_mamba_state = cdiv(mamba_page_size, attn_page_size_1_token)
            chunk_size = lcm(base_chunk_size, kernel_block_alignment_size)
            attn_block_size = chunk_size * cdiv(attn_tokens_per_mamba_state, chunk_size)
            cache_config.mamba_block_size = attn_block_size
        else:
            # Without prefix caching, use minimum block size that satisfies
            # both backend alignment and mamba page size compatibility
            attn_block_size = kernel_block_alignment_size * cdiv(
                mamba_page_size,
                kernel_block_alignment_size * attn_page_size_1_token,
            )

        if cache_config.block_size < attn_block_size:
            cache_config.block_size = attn_block_size
            logger.info(
                "Setting attention block size to %d tokens "
                "to ensure that attention page size is >= mamba page size.",
                attn_block_size,
            )

        if cache_config.mamba_cache_mode == "align":
            cache_config.mamba_block_size = cache_config.block_size

        # Pad mamba page size to exactly match attention page size
        attn_page_size = cache_config.block_size * attn_page_size_1_token
        assert attn_page_size >= mamba_page_size

        if attn_page_size == mamba_page_size:
            return

        if (
            cache_config.mamba_page_size_padded is None
            or cache_config.mamba_page_size_padded != attn_page_size
        ):
            cache_config.mamba_page_size_padded = attn_page_size
            mamba_padding_pct = (
                100 * (attn_page_size - mamba_page_size) / mamba_page_size
            )
            logger.info(
                "Padding mamba page size by %.2f%% to ensure "
                "that mamba page size and attention page size are "
                "exactly equal.",
                mamba_padding_pct,
            )