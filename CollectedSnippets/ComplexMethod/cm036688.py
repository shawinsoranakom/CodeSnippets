def test_backend_selection(
    device: str,
    name: str,
    use_mla: bool,
    block_size: int,
):
    """Test attention backend selection with valid device-backend pairs."""
    # Create AttentionConfig with the specified backend
    attention_config = AttentionConfig(backend=AttentionBackendEnum[name])
    cache_config = CacheConfig(block_size=block_size)
    vllm_config = VllmConfig(
        attention_config=attention_config, cache_config=cache_config
    )

    with set_current_vllm_config(vllm_config):
        if device == "cpu":
            with patch("vllm.platforms.current_platform", CpuPlatform()):
                backend = get_attn_backend(16, torch.float16, None)
            assert backend.get_name() == "CPU_ATTN"

        elif device == "hip":
            if RocmPlatform is None:
                pytest.skip("RocmPlatform not available")
            with patch("vllm.platforms.current_platform", RocmPlatform()):
                if use_mla:
                    # ROCm MLA backend logic:
                    # - TRITON_MLA: supported when block_size != 1
                    # - ROCM_AITER_MLA: supported when block_size == 1
                    # If backend is forced but doesn't match block_size,
                    # should raise ValueError

                    if name == "TRITON_MLA" and block_size == 1:
                        # TRITON_MLA doesn't support block_size == 1
                        with pytest.raises(ValueError):
                            get_attn_backend(576, torch.float16, None, use_mla=use_mla)
                    else:
                        # Valid backend-block_size combination
                        backend = get_attn_backend(
                            576, torch.float16, None, use_mla=use_mla
                        )
                        expected = name
                        assert backend.get_name() == expected
                else:
                    backend = get_attn_backend(32, torch.float16, None, use_mla=use_mla)
                    expected = "ROCM_ATTN"
                    assert backend.get_name() == expected

        elif device == "cuda":
            if CudaPlatform is None:
                pytest.skip("CudaPlatform not available")
            with patch("vllm.platforms.current_platform", CudaPlatform()):
                capability = torch.cuda.get_device_capability()
                if use_mla:
                    # CUDA MLA backend logic:
                    # - CUTLASS_MLA: only supported with block_size == 128
                    #   and Blackwell GPUs (SM 10.x), V1 only
                    # - FLASHINFER_MLA: only supported on Blackwell GPUs
                    #   (SM 10.x), V1 only
                    # - FLASHMLA: only supported with block_size == 64
                    # - FLASH_ATTN_MLA: V1 only
                    # - TRITON_MLA: fallback for other cases

                    if name == "CUTLASS_MLA":
                        if block_size != 128:
                            # CUTLASS_MLA only supports block_size == 128
                            pytest.skip("CUTLASS_MLA only supports block_size 128")
                        if capability[0] != 10:
                            pytest.skip("CUTLASS MLA is not supported on this platform")
                        backend = get_attn_backend(
                            576, torch.float16, None, use_mla=use_mla
                        )
                        expected = "CUTLASS_MLA"
                        assert backend.get_name() == expected
                    elif name == "FLASHINFER_MLA":
                        if capability[0] != 10:
                            pytest.skip(
                                "FlashInfer MLA is not supported on this platform"
                            )
                        if block_size not in [32, 64]:
                            # FlashInfer MLA only supports block_size 32 or 64
                            pytest.skip(
                                "FlashInfer MLA only supports block_size 32 or 64"
                            )
                        backend = get_attn_backend(
                            576, torch.float16, None, use_mla=use_mla
                        )
                        expected = "FLASHINFER_MLA"
                        assert backend.get_name() == expected
                    elif name == "FLASHMLA":
                        if block_size != 64:
                            # FlashMLA only supports block_size == 64
                            pytest.skip("FlashMLA only supports block_size 64")
                        from vllm.v1.attention.backends.mla.flashmla import (
                            is_flashmla_dense_supported,
                        )

                        is_supported, _ = is_flashmla_dense_supported()
                        if not is_supported:
                            pytest.skip("FlashMLA not supported on this platform")
                        backend = get_attn_backend(
                            576,
                            torch.float16,
                            None,
                            use_mla=use_mla,
                        )
                        expected = name
                        assert backend.get_name() == expected
                    elif name == "FLASH_ATTN_MLA":
                        from vllm.v1.attention.backends.fa_utils import (
                            flash_attn_supports_mla,
                        )

                        if not flash_attn_supports_mla():
                            pytest.skip(
                                "FlashAttention MLA not supported on this platform"
                            )
                        backend = get_attn_backend(
                            576, torch.float16, None, use_mla=use_mla
                        )
                        expected = "FLASH_ATTN_MLA"
                        assert backend.get_name() == expected
                    else:
                        # TRITON_MLA or other fallback
                        backend = get_attn_backend(
                            576, torch.float16, None, use_mla=use_mla
                        )
                        expected = "TRITON_MLA"
                        assert backend.get_name() == expected
                elif name == "FLASHINFER":
                    backend = get_attn_backend(64, torch.float16, None, use_mla=use_mla)
                    expected = "FLASHINFER"
                    assert backend.get_name() == expected
                elif name == "FLASH_ATTN":
                    backend = get_attn_backend(32, torch.float16, None, use_mla=use_mla)
                    expected = "FLASH_ATTN"
                    assert backend.get_name() == expected