def test_start_load_caches_consumer_3_items(
        self,
        mock_vllm_config_producer,
        mock_vllm_config_consumer,
        mock_request_with_3_mm,
        temp_storage,
    ):
        """Test consumer loads 3 caches from storage."""
        # First, create producer to save caches
        producer = ECExampleConnector(
            vllm_config=mock_vllm_config_producer,
            role=ECConnectorRole.WORKER,
        )

        # Producer saves 3 caches
        mm_hashes = [f.identifier for f in mock_request_with_3_mm.mm_features]
        saved_caches = {}
        for mm_hash in mm_hashes:
            saved_caches[mm_hash] = torch.randn(10, 768)
            producer.save_caches(saved_caches, mm_hash)

        # Now consumer loads
        consumer = ECExampleConnector(
            vllm_config=mock_vllm_config_consumer,
            role=ECConnectorRole.WORKER,
        )

        # Setup metadata for all 3
        metadata = ECExampleConnectorMetadata()
        for mm_hash in mm_hashes:
            metadata.add_mm_data(MMMeta.make_meta(mm_hash, 100))
        consumer.bind_connector_metadata(metadata)

        # Load
        encoder_cache: dict[str, torch.Tensor] = {}
        consumer.start_load_caches(encoder_cache=encoder_cache)

        # Verify all 3 loaded
        assert len(encoder_cache) == 3
        for mm_hash in mm_hashes:
            assert mm_hash in encoder_cache, f"{mm_hash} missing in encoder_cache"
            assert encoder_cache[mm_hash].is_cuda, (
                f"{mm_hash} cache is in {encoder_cache[mm_hash].device}"
            )
            assert torch.allclose(
                encoder_cache[mm_hash].cpu(), saved_caches[mm_hash]
            ), f"{mm_hash} cache saved and loaded tesnor are not the same"