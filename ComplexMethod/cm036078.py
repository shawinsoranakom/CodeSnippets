def test_is_remote_gguf_with_colon_and_slash(self):
        """Test is_remote_gguf with repo_id:quant_type format."""
        # Valid quant types (exact GGML types)
        assert is_remote_gguf("unsloth/Qwen3-0.6B-GGUF:IQ1_S")
        assert is_remote_gguf("user/repo:Q2_K")
        assert is_remote_gguf("repo/model:Q4_K")
        assert is_remote_gguf("repo/model:Q8_0")

        # Invalid quant types should return False
        assert not is_remote_gguf("repo/model:quant")
        assert not is_remote_gguf("repo/model:INVALID")
        assert not is_remote_gguf("repo/model:invalid_type")