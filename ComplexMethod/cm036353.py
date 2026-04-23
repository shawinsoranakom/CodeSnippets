def test_signature_detection_with_mocking():
    """
    Test that the factory correctly applies compat_sig flag returned from
    _get_connector_class_with_compat.
    """
    vllm_config = create_vllm_config()
    scheduler = create_scheduler(vllm_config)
    kv_cache_config = scheduler.kv_cache_config

    # Mock _get_connector_class_with_compat to return old-style connector
    with patch.object(
        KVConnectorFactory,
        "_get_connector_class_with_compat",
        return_value=(OldStyleTestConnector, True),
    ):
        old_connector = KVConnectorFactory.create_connector(
            vllm_config, KVConnectorRole.SCHEDULER, kv_cache_config
        )
        assert old_connector is not None
        assert isinstance(old_connector, OldStyleTestConnector)
        assert old_connector._kv_cache_config is None

    # Mock _get_connector_class_with_compat to return new-style connector
    with patch.object(
        KVConnectorFactory,
        "_get_connector_class_with_compat",
        return_value=(NewStyleTestConnector, False),
    ):
        new_connector = KVConnectorFactory.create_connector(
            vllm_config, KVConnectorRole.SCHEDULER, kv_cache_config
        )
        assert new_connector is not None
        assert isinstance(new_connector, NewStyleTestConnector)
        assert new_connector._kv_cache_config is not None
        assert new_connector._kv_cache_config == kv_cache_config