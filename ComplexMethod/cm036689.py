def test_fp32_fallback(device: str):
    """Test attention backend selection with fp32."""
    # Use default config (no backend specified)
    vllm_config = VllmConfig()

    with set_current_vllm_config(vllm_config):
        if device == "cpu":
            with patch("vllm.platforms.current_platform", CpuPlatform()):
                backend = get_attn_backend(16, torch.float32, None)
            assert backend.get_name() == "CPU_ATTN"

        elif device == "cuda":
            if CudaPlatform is None:
                pytest.skip("CudaPlatform not available")
            with patch("vllm.platforms.current_platform", CudaPlatform()):
                backend = get_attn_backend(16, torch.float32, None)
            assert backend.get_name() == "FLEX_ATTENTION"

        elif device == "hip":
            if RocmPlatform is None:
                pytest.skip("RocmPlatform not available")
            # ROCm backends do not support head_size=16 (minimum is 32).
            # No known HuggingFace transformer model uses head_size=16.
            # Revisit if a real model with this head size is identified
            # and accuracy-tested.
            with (
                patch("vllm.platforms.current_platform", RocmPlatform()),
                pytest.raises(ValueError, match="No valid attention backend"),
            ):
                get_attn_backend(16, torch.float32, None)