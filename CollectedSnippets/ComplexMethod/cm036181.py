def test_update_state_after_alloc_3_items(
        self, mock_vllm_config_producer, mock_request_with_3_mm
    ):
        """Test state update after allocation for 3 MM items."""
        connector = ECExampleConnector(
            vllm_config=mock_vllm_config_producer,
            role=ECConnectorRole.SCHEDULER,
        )

        # Initial state should be empty
        assert len(connector._mm_datas_need_loads) == 0

        # Update state for all 3 items (mock cache existence)
        with patch.object(connector, "has_cache_item", return_value=True):
            for i in range(3):
                connector.update_state_after_alloc(mock_request_with_3_mm, index=i)

        # Check state updated for all 3
        assert len(connector._mm_datas_need_loads) == 3
        assert "img_hash_1" in connector._mm_datas_need_loads
        assert "img_hash_2" in connector._mm_datas_need_loads
        assert "img_hash_3" in connector._mm_datas_need_loads
        assert connector._mm_datas_need_loads["img_hash_1"] == 100
        assert connector._mm_datas_need_loads["img_hash_2"] == 150
        assert connector._mm_datas_need_loads["img_hash_3"] == 200