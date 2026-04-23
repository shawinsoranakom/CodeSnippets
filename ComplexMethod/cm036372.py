def test_converts_single_event(self, mock_connector, mock_lmcache_engine_event):
        """Test conversion of a single event from lmcache engine format."""
        mock_connector._lmcache_engine.get_kv_events.return_value = [
            mock_lmcache_engine_event
        ]

        result = mock_connector.get_kv_connector_kv_cache_events()

        assert result is not None
        assert isinstance(result, LMCacheKVEvents)
        assert result.get_number_of_workers() == 1

        events = result.get_all_events()
        assert len(events) == 1
        assert isinstance(events[0], BlockStored)
        assert events[0].block_hashes == ["hash1", "hash2"]
        assert events[0].parent_block_hash == "parent_hash"
        assert events[0].token_ids == [1, 2, 3, 4]
        assert events[0].lora_id is None
        assert events[0].block_size == 16
        assert events[0].medium == "GPU"
        assert events[0].lora_name is None