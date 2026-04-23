def test_flash_attn(monkeypatch: pytest.MonkeyPatch):
    """Test FlashAttn validation."""
    pytest.skip(
        "Skipping as current backend selector does not "
        "handle fallbacks when a backend is explicitly set."
    )

    attention_config = AttentionConfig(backend=AttentionBackendEnum.FLASH_ATTN)
    cache_config = CacheConfig(block_size=16)
    vllm_config = VllmConfig(
        attention_config=attention_config, cache_config=cache_config
    )

    with set_current_vllm_config(vllm_config):
        # Unsupported CUDA arch
        monkeypatch.setattr(torch.cuda, "get_device_capability", lambda _=None: (7, 5))
        backend = get_attn_backend(16, torch.float16, None)
        assert backend.get_name() != "FLASH_ATTN"

        # Reset the monkeypatch for subsequent tests
        monkeypatch.undo()

        # Unsupported data type
        backend = get_attn_backend(16, torch.float8_e4m3fn, None)
        assert backend.get_name() != "FLASH_ATTN"

        # Unsupported kv cache data type
        backend = get_attn_backend(16, torch.float16, "fp8")
        assert backend.get_name() != "FLASH_ATTN"

        # Unsupported block size
        vllm_config.cache_config.block_size = 8
        backend = get_attn_backend(16, torch.float16, None)
        assert backend.get_name() != "FLASH_ATTN"

        # flash-attn is not installed
        import sys

        vllm_config.cache_config.block_size = 16
        original_module = sys.modules.get("vllm_flash_attn")
        monkeypatch.setitem(sys.modules, "vllm_flash_attn", None)
        backend = get_attn_backend(16, torch.float16, None)
        assert backend.get_name() != "FLASH_ATTN"

        # Restore the original module if it existed
        if original_module is not None:
            monkeypatch.setitem(sys.modules, "vllm_flash_attn", original_module)
        else:
            monkeypatch.delitem(sys.modules, "vllm_flash_attn", raising=False)

        # Unsupported head size
        backend = get_attn_backend(17, torch.float16, None)
        assert backend.get_name() != "FLASH_ATTN"