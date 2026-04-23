async def test_store_manager_cleanup_after_stop(
    tmpdir: py.path.local, freezer: FrozenDateTimeFactory
) -> None:
    """Test that the cache is cleaned up after stop event.

    This should only happen if we stop within the cleanup delay.
    """
    loop = asyncio.get_running_loop()

    def _setup_mock_storage():
        config_dir = tmpdir.mkdir("temp_config")
        tmp_storage = config_dir.mkdir(".storage")
        tmp_storage.join("integration1").write_binary(
            json_bytes({"data": {"integration1": "integration1"}, "version": 1})
        )
        tmp_storage.join("integration2").write_binary(
            json_bytes({"data": {"integration2": "integration2"}, "version": 1})
        )
        return config_dir

    config_dir = await loop.run_in_executor(None, _setup_mock_storage)

    async with async_test_home_assistant(config_dir=config_dir.strpath) as hass:
        hass.set_state(CoreState.not_running)
        store_manager = storage.get_internal_store_manager(hass)
        await store_manager.async_initialize()
        await store_manager.async_preload(["integration1", "integration2"])
        assert "integration1" in store_manager._data_preload
        assert "integration2" in store_manager._data_preload
        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()
        assert "integration1" in store_manager._data_preload
        assert "integration2" in store_manager._data_preload
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await hass.async_block_till_done()
        assert "integration1" in store_manager._data_preload
        assert "integration2" in store_manager._data_preload
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        await hass.async_block_till_done()
        assert "integration1" not in store_manager._data_preload
        assert "integration2" not in store_manager._data_preload
        assert store_manager.async_fetch("integration1") is None
        assert store_manager.async_fetch("integration2") is None
        await hass.async_stop(force=True)