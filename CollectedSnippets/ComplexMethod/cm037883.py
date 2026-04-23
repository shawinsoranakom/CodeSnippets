def verify_and_update_config(vllm_config: "VllmConfig") -> None:
        """Force unified attention backend for models with heterogeneous
        head dimensions.

        Some Gemma4 variants use different head dimensions for
        sliding window (head_dim) vs full attention (global_head_dim) layers.
        When global_head_dim > 256, FlashAttention rejects those layers
        (head_size <= 256 kernel limit), causing vLLM to select a different
        backend for each layer type. This mixed-backend execution produces
        numerical divergence and output corruption.

        The fix detects heterogeneous head dimensions from the model config
        and forces TRITON_ATTN (which has no head_size ceiling) for all
        layers when the user hasn't explicitly chosen a backend.

        TODO: Heterogeneous head_sizes (head_dim != global_head_dim)
        require NixlConnector changes to support per-layer KV transfer
        with different head dimensions for prefill-decode disaggregation.
        """
        hf_text_config = vllm_config.model_config.hf_text_config
        head_dim = getattr(hf_text_config, "head_dim", None)
        global_head_dim = getattr(hf_text_config, "global_head_dim", None)

        # Only force Triton when head dimensions actually differ AND the
        # larger one exceeds FlashAttention's kernel limit (head_size <= 256).
        # This avoids unnecessary backend forcing on smaller models where
        # the config carries global_head_dim but all layers can still use
        # the same FA backend.
        max_head_dim = max(head_dim or 0, global_head_dim or 0)
        if (
            head_dim is not None
            and global_head_dim is not None
            and head_dim != global_head_dim
            and max_head_dim > 256
            and vllm_config.attention_config.backend is None
        ):
            from vllm.v1.attention.backends.registry import (
                AttentionBackendEnum,
            )

            vllm_config.attention_config.backend = AttentionBackendEnum.TRITON_ATTN
            logger.info(
                "Gemma4 model has heterogeneous head dimensions "
                "(head_dim=%d, global_head_dim=%d). Forcing TRITON_ATTN "
                "backend to prevent mixed-backend numerical divergence.",
                head_dim,
                global_head_dim,
            )