def test_all_13_fields_parsed_together(self):
        fields = {
            "context_length": 131072,
            "block_count": 62,
            "attention.head_count_kv": 16,
            "attention.head_count": 32,
            "embedding_length": 5376,
            "attention.key_length": 128,
            "attention.value_length": 128,
            "attention.sliding_window": 1024,
            "full_attention_interval": 6,
            "attention.kv_lora_rank": 512,
            "attention.key_length_mla": 256,
            "ssm.inner_size": 4096,
            "ssm.state_size": 128,
        }
        b = _backend_from_gguf("testarch", fields)
        assert b._context_length == 131072
        assert b._n_layers == 62
        assert b._n_kv_heads == 16
        assert b._n_heads == 32
        assert b._embedding_length == 5376
        assert b._kv_key_length == 128
        assert b._kv_value_length == 128
        assert b._sliding_window == 1024
        assert b._full_attention_interval == 6
        assert b._kv_lora_rank == 512
        assert b._key_length_mla == 256
        assert b._ssm_inner_size == 4096
        assert b._ssm_state_size == 128