def get_attn_backend_cls(
        cls,
        selected_backend: "AttentionBackendEnum",
        attn_selector_config: "AttentionSelectorConfig",
        num_heads: int | None = None,
    ) -> str:
        from vllm.v1.attention.backends.utils import set_kv_cache_layout

        set_kv_cache_layout("NHD")
        logger.info(
            "Setting VLLM_KV_CACHE_LAYOUT to 'NHD' for XPU; "
            "only NHD layout is supported by XPU attention kernels."
        )

        # TurboQuant KV cache: route directly to TQ backend
        kv_cache_dtype = attn_selector_config.kv_cache_dtype
        if kv_cache_dtype is not None and kv_cache_dtype.startswith("turboquant_"):
            logger.info_once("Using TurboQuant attention backend.")
            return AttentionBackendEnum.TURBOQUANT.get_path()

        dtype = attn_selector_config.dtype
        if attn_selector_config.use_sparse:
            logger.info_once("Using XPU MLA Sparse backend.")
            return AttentionBackendEnum.XPU_MLA_SPARSE.get_path()
        if attn_selector_config.use_mla:
            logger.info_once("Using Triton MLA backend on V1 engine.")
            return AttentionBackendEnum.TRITON_MLA.get_path()
        if selected_backend == AttentionBackendEnum.TRITON_ATTN:
            logger.info_once("Using Triton backend.")
            return AttentionBackendEnum.TRITON_ATTN.get_path()
        elif dtype == torch.float32:
            logger.warning_once(
                "Flash Attention on XPU does not support float32 dtype. "
                "Falling back to Triton Attention backend."
            )
            return AttentionBackendEnum.TRITON_ATTN.get_path()
        elif selected_backend == AttentionBackendEnum.FLASH_ATTN:
            logger.info_once("Using Flash Attention backend.")
            return AttentionBackendEnum.FLASH_ATTN.get_path()
        elif selected_backend:
            raise ValueError(
                f"Invalid attention backend for {cls.device_name}, "
                f"with use_mla: {attn_selector_config.use_mla}"
            )

        logger.info("Using Flash Attention backend.")
        return AttentionBackendEnum.FLASH_ATTN.get_path()