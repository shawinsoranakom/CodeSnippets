def test_preserves_event_attributes(self, mock_connector):
        """Test that all event attributes are correctly preserved."""

        class MockEventWithLora:
            def __init__(self):
                self.block_hashes = ["hash_a", "hash_b", "hash_c"]
                self.parent_block_hash = "parent_xyz"
                self.token_ids = [100, 200, 300]
                self.lora_id = 42
                self.block_size = 32
                self.medium = "DISK"
                self.lora_name = "lora_example"

        mock_connector._lmcache_engine.get_kv_events.return_value = [
            MockEventWithLora()
        ]

        result = mock_connector.get_kv_connector_kv_cache_events()

        events = result.get_all_events()
        event = events[0]

        assert event.block_hashes == ["hash_a", "hash_b", "hash_c"]
        assert event.parent_block_hash == "parent_xyz"
        assert event.token_ids == [100, 200, 300]
        assert event.lora_id == 42
        assert event.block_size == 32
        assert event.medium == "DISK"
        assert event.lora_name == "lora_example"