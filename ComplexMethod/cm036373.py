def test_converts_multiple_events(self, mock_connector):
        """Test conversion of multiple events from lmcache engine format."""

        class MockEvent:
            def __init__(self, i):
                self.block_hashes = [f"hash{i}"]
                self.parent_block_hash = f"parent{i}"
                self.token_ids = [i]
                self.lora_id = None
                self.block_size = 16
                self.medium = "GPU"
                self.lora_name = None

        events = [MockEvent(i) for i in range(5)]
        mock_connector._lmcache_engine.get_kv_events.return_value = events

        result = mock_connector.get_kv_connector_kv_cache_events()

        assert result is not None
        assert isinstance(result, LMCacheKVEvents)

        converted_events = result.get_all_events()
        assert len(converted_events) == 5

        for i, event in enumerate(converted_events):
            assert isinstance(event, BlockStored)
            assert event.block_hashes == [f"hash{i}"]
            assert event.parent_block_hash == f"parent{i}"
            assert event.token_ids == [i]