def test_is_remote_gguf_nonstandard_quant_type(self):
        """Test is_remote_gguf with non-standard quant types containing
        a known GGML type."""
        # Non-standard quant types with known GGML type after prefix
        assert is_remote_gguf("unsloth/Qwen3.5-35B-A3B-GGUF:UD-Q4_K_XL")
        assert is_remote_gguf("user/Model:UD-Q4_K_M")
        assert is_remote_gguf("user/SomeModel:Custom-Q8_0")

        # Exact GGML type after prefix (no suffix stripping needed)
        assert is_remote_gguf("user/Model-GGUF:UD-IQ4_NL")
        assert is_remote_gguf("user/Model-GGUF:UD-Q8_0")

        # Completely unknown quant types should still fail
        assert not is_remote_gguf("repo/model:TOTALLY-RANDOM")
        assert not is_remote_gguf("user/Model:UD-INVALID")

        # No dash separator → not recognized as prefixed
        assert not is_remote_gguf("repo/model:UDIQ4NL")