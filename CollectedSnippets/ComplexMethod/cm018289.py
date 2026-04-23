async def test_dynamic_devices(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    xbox_live_client: AsyncMock,
    device_registry: dr.DeviceRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test adding of new and removal of stale devices at runtime."""

    xbox_live_client.smartglass.get_console_list.return_value = SmartglassConsoleList(
        **await async_load_json_object_fixture(
            hass, "smartglass_console_list_empty.json", DOMAIN
        )  # pyright: ignore[reportArgumentType]
    )

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    assert device_registry.async_get_device({(DOMAIN, "ABCDEFG")}) is None
    assert device_registry.async_get_device({(DOMAIN, "HIJKLMN")}) is None

    xbox_live_client.smartglass.get_console_list.return_value = SmartglassConsoleList(
        **await async_load_json_object_fixture(
            hass, "smartglass_console_list.json", DOMAIN
        )  # pyright: ignore[reportArgumentType]
    )

    freezer.tick(timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert device_registry.async_get_device({(DOMAIN, "ABCDEFG")})
    assert device_registry.async_get_device({(DOMAIN, "HIJKLMN")})

    xbox_live_client.smartglass.get_console_list.return_value = SmartglassConsoleList(
        **await async_load_json_object_fixture(
            hass, "smartglass_console_list_empty.json", DOMAIN
        )  # pyright: ignore[reportArgumentType]
    )

    freezer.tick(timedelta(minutes=10))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert device_registry.async_get_device({(DOMAIN, "ABCDEFG")}) is None
    assert device_registry.async_get_device({(DOMAIN, "HIJKLMN")}) is None