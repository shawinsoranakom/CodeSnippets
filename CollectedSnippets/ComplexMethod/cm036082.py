def test_is_gguf_edge_cases(self):
        """Test is_gguf with edge cases."""
        # Empty string
        assert not is_gguf("")

        # Only colon, no slash (even with valid quant_type)
        assert not is_gguf("model:IQ1_S")

        # Only slash, no colon
        assert not is_gguf("repo/model")

        # HTTP/HTTPS URLs
        assert not is_gguf("http://repo/model:IQ1_S")
        assert not is_gguf("https://repo/model:Q2_K")

        # Cloud storage
        assert not is_gguf("s3://bucket/repo/model:IQ1_S")
        assert not is_gguf("gs://bucket/repo/model:Q2_K")