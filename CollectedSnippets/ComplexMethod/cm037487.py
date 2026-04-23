def _get_backend_priorities(
    use_mla: bool,
    device_capability: DeviceCapability,
    num_heads: int | None = None,
    kv_cache_dtype: CacheDType | None = None,
) -> list[AttentionBackendEnum]:
    """Get backend priorities with lazy import to avoid circular dependency."""
    if use_mla:
        if device_capability.major == 10:
            # Sparse MLA backend priorities
            # See https://github.com/vllm-project/vllm/issues/35807 for
            # benchmark results
            if kv_cache_dtype is not None and is_quantized_kv_cache(kv_cache_dtype):
                # Prefer FlashInfer for fp8 kv cache
                sparse_backends = [
                    AttentionBackendEnum.FLASHINFER_MLA_SPARSE,
                    AttentionBackendEnum.FLASHMLA_SPARSE,
                ]
            else:
                # BF16 KV Cache
                # Prefer FlashInfer at low head counts (FlashMLA uses padding)
                if num_heads is not None and num_heads <= 16:
                    sparse_backends = [
                        AttentionBackendEnum.FLASHINFER_MLA_SPARSE,
                        AttentionBackendEnum.FLASHMLA_SPARSE,
                    ]
                else:
                    sparse_backends = [
                        AttentionBackendEnum.FLASHMLA_SPARSE,
                        AttentionBackendEnum.FLASHINFER_MLA_SPARSE,
                    ]

            return [
                AttentionBackendEnum.FLASHINFER_MLA,
                AttentionBackendEnum.CUTLASS_MLA,
                AttentionBackendEnum.FLASH_ATTN_MLA,
                AttentionBackendEnum.FLASHMLA,
                AttentionBackendEnum.TRITON_MLA,
                *sparse_backends,
            ]
        else:
            return [
                AttentionBackendEnum.FLASH_ATTN_MLA,
                AttentionBackendEnum.FLASHMLA,
                AttentionBackendEnum.FLASHINFER_MLA,
                AttentionBackendEnum.TRITON_MLA,
                AttentionBackendEnum.FLASHMLA_SPARSE,
            ]
    else:
        if device_capability.major == 10:
            return [
                AttentionBackendEnum.FLASHINFER,
                AttentionBackendEnum.FLASH_ATTN,
                AttentionBackendEnum.TRITON_ATTN,
                AttentionBackendEnum.FLEX_ATTENTION,
                AttentionBackendEnum.TURBOQUANT,
            ]
        else:
            return [
                AttentionBackendEnum.FLASH_ATTN,
                AttentionBackendEnum.FLASHINFER,
                AttentionBackendEnum.TRITON_ATTN,
                AttentionBackendEnum.FLEX_ATTENTION,
                AttentionBackendEnum.TURBOQUANT,
            ]