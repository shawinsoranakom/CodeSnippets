def test_build_connector_meta_3_items(
        self, mock_vllm_config_producer, mock_request_with_3_mm
    ):
        """Test metadata building for 3 MM items."""
        connector = ECExampleConnector(
            vllm_config=mock_vllm_config_producer,
            role=ECConnectorRole.SCHEDULER,
        )

        # Setup state for all 3 items (mock cache existence)
        with patch.object(connector, "has_cache_item", return_value=True):
            for i in range(3):
                connector.update_state_after_alloc(mock_request_with_3_mm, index=i)

        # Build metadata
        scheduler_output = Mock(spec=SchedulerOutput)
        metadata = connector.build_connector_meta(scheduler_output)

        # Assert
        assert isinstance(metadata, ECExampleConnectorMetadata)
        assert len(metadata.mm_datas) == 3
        assert metadata.mm_datas[0].mm_hash == "img_hash_1"
        assert metadata.mm_datas[0].num_token == 100
        assert metadata.mm_datas[1].mm_hash == "img_hash_2"
        assert metadata.mm_datas[1].num_token == 150
        assert metadata.mm_datas[2].mm_hash == "img_hash_3"
        assert metadata.mm_datas[2].num_token == 200

        # State should be cleared after building
        assert len(connector._mm_datas_need_loads) == 0