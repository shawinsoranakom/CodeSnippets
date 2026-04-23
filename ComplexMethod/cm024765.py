async def test_ip_changes_fallback_discovery(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test Yeelight ip changes and we fallback to discovery."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_ID: ID, CONF_HOST: "5.5.5.5"}, unique_id=ID
    )
    config_entry.add_to_hass(hass)

    mocked_fail_bulb = _mocked_bulb(cannot_connect=True)
    mocked_fail_bulb.bulb_type = BulbType.WhiteTempMood
    with (
        patch(f"{MODULE}.AsyncBulb", return_value=mocked_fail_bulb),
        _patch_discovery(),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

        assert config_entry.state is ConfigEntryState.SETUP_RETRY
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=2))
        await hass.async_block_till_done(wait_background_tasks=True)

    # The discovery should update the ip address
    assert config_entry.data[CONF_HOST] == IP_ADDRESS
    assert config_entry.state is ConfigEntryState.SETUP_RETRY
    mocked_bulb = _mocked_bulb()

    with patch(f"{MODULE}.AsyncBulb", return_value=mocked_bulb), _patch_discovery():
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=10))
        await hass.async_block_till_done(wait_background_tasks=True)
        assert config_entry.state is ConfigEntryState.LOADED

    binary_sensor_entity_id = ENTITY_BINARY_SENSOR_TEMPLATE.format(
        f"yeelight_color_{SHORT_ID}"
    )
    assert entity_registry.async_get(binary_sensor_entity_id) is not None

    # Make sure we can still reload with the new ip right after we change it
    with patch(f"{MODULE}.AsyncBulb", return_value=mocked_bulb), _patch_discovery():
        await hass.config_entries.async_reload(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert entity_registry.async_get(binary_sensor_entity_id) is not None