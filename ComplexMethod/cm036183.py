def test_save_caches_producer_3_items(
        self, mock_vllm_config_producer, mock_request_with_3_mm, temp_storage
    ):
        """Test cache saving as producer for 3 different MM items."""
        connector = ECExampleConnector(
            vllm_config=mock_vllm_config_producer,
            role=ECConnectorRole.WORKER,
        )

        # Create and save 3 different caches
        mm_hashes = [f.identifier for f in mock_request_with_3_mm.mm_features]
        encoder_cache: dict[str, torch.Tensor] = {}

        for mm_hash in mm_hashes:
            encoder_cache[mm_hash] = torch.randn(10, 768)
            connector.save_caches(encoder_cache, mm_hash)

        # Verify all files exist using has_cache_item
        result = [
            connector.has_cache_item(mm_feature.identifier)
            for mm_feature in mock_request_with_3_mm.mm_features
        ]
        assert all(result), f"Not all caches were saved: {result}"

        # Verify each file's content
        for mm_hash in mm_hashes:
            filename = connector._generate_filename_debug(mm_hash)
            loaded = safetensors.torch.load_file(filename)
            assert "ec_cache" in loaded
            assert torch.allclose(loaded["ec_cache"], encoder_cache[mm_hash].cpu())