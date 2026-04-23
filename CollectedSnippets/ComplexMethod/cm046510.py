def test_reset_between_parses(self):
        # First parse with all fields
        b = _backend_from_gguf(
            "arch1",
            {
                "block_count": 32,
                "attention.key_length": 128,
                "attention.kv_lora_rank": 512,
                "ssm.inner_size": 4096,
            },
        )
        assert b._kv_key_length == 128
        assert b._kv_lora_rank == 512
        assert b._ssm_inner_size == 4096

        # Second parse without those fields -- they should be None
        kv = {"general.architecture": "arch2", "arch2.block_count": 64}
        import tempfile, os

        data = _make_gguf_bytes("arch2", kv)
        fd, path = tempfile.mkstemp(suffix = ".gguf")
        os.write(fd, data)
        os.close(fd)
        try:
            b._read_gguf_metadata(path)
        finally:
            os.unlink(path)
        assert b._kv_key_length is None
        assert b._kv_lora_rank is None
        assert b._ssm_inner_size is None
        assert b._n_layers == 64