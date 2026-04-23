def test_per_head_quant_scales_backend_selection(
    backend_name: str, flash_attn_version: int | None, should_succeed: bool
):
    """Test backend selection when use_per_head_quant_scales=True."""
    # Clear cache to ensure fresh backend selection
    _cached_get_attn_backend.cache_clear()

    attention_config = AttentionConfig(
        backend=AttentionBackendEnum[backend_name],
        flash_attn_version=flash_attn_version,
    )
    cache_config = CacheConfig(block_size=64)
    vllm_config = VllmConfig(
        attention_config=attention_config, cache_config=cache_config
    )

    if CudaPlatform is None:
        pytest.skip("CudaPlatform not available")
    with (
        set_current_vllm_config(vllm_config),
        patch("vllm.platforms.current_platform", CudaPlatform()),
    ):
        if backend_name == "FLASH_ATTN" and flash_attn_version == 3:
            if not torch.cuda.is_available():
                pytest.skip("FA3 requires CUDA")
            capability = torch.cuda.get_device_capability()
            if capability[0] != 9:
                pytest.skip("FA3 is only supported on Hopper (SM 9.x) GPUs")

        if should_succeed:
            backend = get_attn_backend(
                head_size=128,
                dtype=torch.float16,
                kv_cache_dtype="fp8",
                use_per_head_quant_scales=True,
            )
            assert backend.get_name() == backend_name
        else:
            with pytest.raises(ValueError) as exc_info:
                get_attn_backend(
                    head_size=128,
                    dtype=torch.float16,
                    kv_cache_dtype="fp8",
                    use_per_head_quant_scales=True,
                )
            assert backend_name in str(exc_info.value)