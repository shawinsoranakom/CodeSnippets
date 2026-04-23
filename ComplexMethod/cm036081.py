def test_is_gguf_with_remote_gguf(self):
        """Test is_gguf with remote GGUF format."""
        # Valid remote GGUF format (repo_id:quant_type with valid quant_type)
        assert is_gguf("unsloth/Qwen3-0.6B-GGUF:IQ1_S")
        assert is_gguf("repo/model:Q2_K")
        assert is_gguf("repo/model:Q4_K")

        # Extended quant types with suffixes
        assert is_gguf("repo/model:Q4_K_M")
        assert is_gguf("repo/model:Q3_K_S")
        assert is_gguf("repo/model:Q5_K_L")

        # Invalid quant_type should return False
        assert not is_gguf("repo/model:quant")
        assert not is_gguf("repo/model:INVALID")