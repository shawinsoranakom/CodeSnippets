def validate_configuration(
        cls,
        head_size: int,
        dtype: torch.dtype,
        kv_cache_dtype: "CacheDType | None",
        block_size: int | None,
        use_mla: bool,
        has_sink: bool,
        use_sparse: bool,
        use_mm_prefix: bool,
        use_per_head_quant_scales: bool,
        device_capability: "DeviceCapability",
        attn_type: str,
        use_non_causal: bool = False,
    ) -> list[str]:
        invalid_reasons = []
        if not cls.supports_head_size(head_size):
            invalid_reasons.append("head_size not supported")
        if not cls.supports_dtype(dtype):
            invalid_reasons.append("dtype not supported")
        if not cls.supports_kv_cache_dtype(kv_cache_dtype):
            invalid_reasons.append("kv_cache_dtype not supported")
        if not cls.supports_block_size(block_size):
            invalid_reasons.append("block_size not supported")
        if use_mm_prefix and not cls.supports_mm_prefix():
            invalid_reasons.append(
                "partial multimodal token full attention not supported"
            )
        if use_mla != cls.is_mla():
            if use_mla:
                invalid_reasons.append("MLA not supported")
            else:
                invalid_reasons.append("non-MLA not supported")
        if has_sink and not cls.supports_sink():
            invalid_reasons.append("attention sinks not supported")
        if use_sparse != cls.is_sparse():
            if use_sparse:
                invalid_reasons.append("sparse not supported")
            else:
                invalid_reasons.append("non-sparse not supported")
        if use_per_head_quant_scales and not cls.supports_per_head_quant_scales():
            invalid_reasons.append("per-head quant scales not supported")
        if not cls.supports_compute_capability(device_capability):
            invalid_reasons.append("compute capability not supported")
        if not cls.supports_attn_type(attn_type):
            invalid_reasons.append(f"attention type {attn_type} not supported")
        if use_non_causal and not cls.supports_non_causal():
            invalid_reasons.append("non-causal attention not supported")
        combination_reason = cls.supports_combination(
            head_size,
            dtype,
            kv_cache_dtype,
            block_size,
            use_mla,
            has_sink,
            use_sparse,
            device_capability,
        )
        if combination_reason is not None:
            invalid_reasons.append(combination_reason)
        return invalid_reasons