async def test_store_manager_caching(
    tmpdir: py.path.local, caplog: pytest.LogCaptureFixture
) -> None:
    """Test store manager caching."""
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
        tmp_storage.join("broken").write_binary(b"invalid")
        return config_dir

    config_dir = await loop.run_in_executor(None, _setup_mock_storage)

    async with async_test_home_assistant(config_dir=config_dir.strpath) as hass:
        store_manager = storage.get_internal_store_manager(hass)
        assert (
            store_manager.async_fetch("integration1") is None
        )  # has data but not cached
        assert (
            store_manager.async_fetch("integration2") is None
        )  # has data but not cached
        assert (
            store_manager.async_fetch("integration3") is None
        )  # no file not but cached

        await store_manager.async_initialize()
        assert (
            store_manager.async_fetch("integration1") is None
        )  # has data but not cached
        assert (
            store_manager.async_fetch("integration2") is None
        )  # has data but not cached
        assert (
            store_manager.async_fetch("integration3") is not None
        )  # no file and initialized

        result = store_manager.async_fetch("integration3")
        assert result is not None
        exists, data = result
        assert exists is False
        assert data is None

        await store_manager.async_preload(["integration3", "integration2", "broken"])
        assert "Error loading broken" in caplog.text

        assert (
            store_manager.async_fetch("integration1") is None
        )  # has data but not cached
        result = store_manager.async_fetch("integration2")
        assert result is not None
        exists, data = result
        assert exists is True
        assert data == {"data": {"integration2": "integration2"}, "version": 1}

        assert (
            store_manager.async_fetch("integration3") is not None
        )  # no file and initialized
        result = store_manager.async_fetch("integration3")
        assert result is not None
        exists, data = result
        assert exists is False
        assert data is None

        integration1 = storage.Store(hass, 1, "integration1")
        await integration1.async_save({"integration1": "updated"})
        # Save should invalidate the cache
        assert store_manager.async_fetch("integration1") is None  # invalidated

        integration2 = storage.Store(hass, 1, "integration2")
        integration2.async_delay_save(lambda: {"integration2": "updated"})
        # Delay save should invalidate the cache after it saves
        assert "integration2" not in store_manager._invalidated

        # Block twice to flush out the delayed save
        await hass.async_block_till_done()
        await hass.async_block_till_done()
        assert store_manager.async_fetch("integration2") is None  # invalidated

        store_manager.async_invalidate("integration3")
        assert store_manager.async_fetch("integration1") is None  # invalidated by save
        assert (
            store_manager.async_fetch("integration2") is None
        )  # invalidated by delay save
        assert store_manager.async_fetch("integration3") is None  # invalidated

        await hass.async_stop(force=True)

    async with async_test_home_assistant(config_dir=config_dir.strpath) as hass:
        store_manager = storage.get_internal_store_manager(hass)
        assert store_manager.async_fetch("integration1") is None
        assert store_manager.async_fetch("integration2") is None
        assert store_manager.async_fetch("integration3") is None
        await store_manager.async_initialize()
        await store_manager.async_preload(["integration1", "integration2"])
        result = store_manager.async_fetch("integration1")
        assert result is not None
        exists, data = result
        assert exists is True
        assert data["data"] == {"integration1": "updated"}

        integration1 = storage.Store(hass, 1, "integration1")
        assert await integration1.async_load() == {"integration1": "updated"}

        # Load should pop the cache
        assert store_manager.async_fetch("integration1") is None

        integration2 = storage.Store(hass, 1, "integration2")
        assert await integration2.async_load() == {"integration2": "updated"}

        # Load should pop the cache
        assert store_manager.async_fetch("integration2") is None

        integration3 = storage.Store(hass, 1, "integration3")
        assert await integration3.async_load() is None

        await integration3.async_save({"integration3": "updated"})
        assert await integration3.async_load() == {"integration3": "updated"}

        await hass.async_stop(force=True)

    # Now make sure everything still works when we do not
    # manually load the storage manager
    async with async_test_home_assistant(config_dir=config_dir.strpath) as hass:
        integration1 = storage.Store(hass, 1, "integration1")
        assert await integration1.async_load() == {"integration1": "updated"}
        await integration1.async_save({"integration1": "updated2"})
        assert await integration1.async_load() == {"integration1": "updated2"}

        integration2 = storage.Store(hass, 1, "integration2")
        assert await integration2.async_load() == {"integration2": "updated"}
        await integration2.async_save({"integration2": "updated2"})
        assert await integration2.async_load() == {"integration2": "updated2"}

        await hass.async_stop(force=True)

    # Now remove the stores
    async with async_test_home_assistant(config_dir=config_dir.strpath) as hass:
        store_manager = storage.get_internal_store_manager(hass)
        await store_manager.async_initialize()
        await store_manager.async_preload(["integration1", "integration2"])

        integration1 = storage.Store(hass, 1, "integration1")
        assert integration1._manager is store_manager
        assert await integration1.async_load() == {"integration1": "updated2"}

        integration2 = storage.Store(hass, 1, "integration2")
        assert integration2._manager is store_manager
        assert await integration2.async_load() == {"integration2": "updated2"}

        await integration1.async_remove()
        await integration2.async_remove()

        assert store_manager.async_fetch("integration1") is None
        assert store_manager.async_fetch("integration2") is None

        assert await integration1.async_load() is None
        assert await integration2.async_load() is None

        await hass.async_stop(force=True)

    # Now make sure the stores are removed and another run works
    async with async_test_home_assistant(config_dir=config_dir.strpath) as hass:
        store_manager = storage.get_internal_store_manager(hass)
        await store_manager.async_initialize()
        await store_manager.async_preload(["integration1"])
        result = store_manager.async_fetch("integration1")
        assert result is not None
        exists, data = result
        assert exists is False
        assert data is None
        await hass.async_stop(force=True)