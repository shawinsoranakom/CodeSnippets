def test_has_cache_item_all_exist_3_items(
        self,
        mock_vllm_config_producer,
        mock_vllm_config_consumer,
        mock_request_with_3_mm,
    ):
        """Test has_cache_item returns True when all 3 caches exist."""
        # Test for producer first
        producer = ECExampleConnector(
            vllm_config=mock_vllm_config_producer,
            role=ECConnectorRole.SCHEDULER,
        )

        # Create cache files using save_caches (proper way)
        encoder_cache: dict[str, torch.Tensor] = {}

        for mm_feature in mock_request_with_3_mm.mm_features:
            mm_hash = mm_feature.identifier
            encoder_cache[mm_hash] = torch.randn(10, 768)
            producer.save_caches(encoder_cache, mm_hash)

        # Test using has_cache_item API
        producer_result = [
            producer.has_cache_item(mm_feature.identifier)
            for mm_feature in mock_request_with_3_mm.mm_features
        ]

        # Assert
        assert len(producer_result) == 3
        assert all(producer_result), f"Expected all True, got {producer_result}"

        # Also test consumer can check if cache exists
        consumer = ECExampleConnector(
            vllm_config=mock_vllm_config_consumer,
            role=ECConnectorRole.SCHEDULER,
        )

        # Test using has_cache_item API
        consumer_result = [
            consumer.has_cache_item(mm_feature.identifier)
            for mm_feature in mock_request_with_3_mm.mm_features
        ]

        # Assert
        assert len(consumer_result) == 3
        assert all(consumer_result), f"Expected all True, got {consumer_result}"