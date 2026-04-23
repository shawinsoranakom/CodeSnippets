def test_is_remote_gguf_extended_quant_types(self):
        """Test is_remote_gguf with extended quant type naming conventions."""
        # Extended quant types with _M, _S, _L suffixes
        assert is_remote_gguf("repo/model:Q4_K_M")
        assert is_remote_gguf("repo/model:Q4_K_S")
        assert is_remote_gguf("repo/model:Q3_K_L")
        assert is_remote_gguf("repo/model:Q5_K_M")
        assert is_remote_gguf("repo/model:Q3_K_S")

        # Extended quant types with _XL, _XS, _XXS suffixes
        assert is_remote_gguf("repo/model:Q5_K_XL")
        assert is_remote_gguf("repo/model:IQ4_XS")
        assert is_remote_gguf("repo/model:IQ3_XXS")

        # Invalid extended types (base type doesn't exist)
        assert not is_remote_gguf("repo/model:INVALID_M")
        assert not is_remote_gguf("repo/model:Q9_K_M")