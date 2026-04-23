def test_mha_attn_platform(default_vllm_config, device: str):
    """
    Test the attention selector between different platform and device.
    """
    torch.set_default_dtype(torch.float16)

    if device == "cpu":
        with (
            patch("vllm.model_executor.models.vision.current_platform", CpuPlatform()),
        ):
            attn = MMEncoderAttention(16, 64, scale=1)
            assert attn.attn_backend == AttentionBackendEnum.TORCH_SDPA
    elif device == "hip":
        with (
            patch("vllm.model_executor.models.vision.current_platform", RocmPlatform()),
        ):
            attn = MMEncoderAttention(16, 64, scale=1)
            assert attn.attn_backend == AttentionBackendEnum.FLASH_ATTN
    else:
        # Test CUDA with head_size=64 (divisible by 32)
        # - should use vLLM's FlashAttention
        with (
            patch("vllm.model_executor.models.vision.current_platform", CudaPlatform()),
        ):
            attn = MMEncoderAttention(16, 64, scale=1)
            assert attn.attn_backend == AttentionBackendEnum.FLASH_ATTN

        # Test CUDA with head_size=72 (not divisible by 32)
        # - should use vLLM's FlashAttention
        with (
            patch("vllm.model_executor.models.vision.current_platform", CudaPlatform()),
        ):
            attn = MMEncoderAttention(16, 72, scale=1)
            assert attn.attn_backend == AttentionBackendEnum.FLASH_ATTN

        # Test CUDA with head_size=72 (not divisible by 32)
        # - should use vLLM's FlashAttention
        with (
            patch("vllm.model_executor.models.vision.current_platform", CudaPlatform()),
            set_default_torch_dtype(torch.float32),
        ):
            attn = MMEncoderAttention(16, 72, scale=1)
            assert attn.attn_backend == AttentionBackendEnum.TRITON_ATTN

        # Test Turing (pre-Ampere, sm_75): FlashAttention requires sm>=80,
        # and Triton no longer supports MMA on Turing, so we expect that
        # TORCH_SDPA is used for MMEncoderAttention.
        with (
            patch("vllm.model_executor.models.vision.current_platform", CudaPlatform()),
            patch.object(
                CudaPlatform,
                "get_device_capability",
                return_value=DeviceCapability(major=7, minor=5),
            ),
        ):
            attn = MMEncoderAttention(16, 64, scale=1)
            assert attn.attn_backend == AttentionBackendEnum.TORCH_SDPA