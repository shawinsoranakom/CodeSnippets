async def test_default_entity_and_device_name(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    caplog: pytest.LogCaptureFixture,
    entity_id: str,
    friendly_name: str,
    device_name: str | None,
    assert_log: bool,
) -> None:
    """Test device name setup with and without a device_class set.

    This is a test helper for the _setup_common_attributes_from_config mixin.
    """

    events = async_capture_events(hass, ir.EVENT_REPAIRS_ISSUE_REGISTRY_UPDATED)
    hass.set_state(CoreState.starting)
    await hass.async_block_till_done()

    entry = MockConfigEntry(
        domain=mqtt.DOMAIN,
        data={mqtt.CONF_BROKER: "mock-broker"},
        version=mqtt.CONFIG_ENTRY_VERSION,
        minor_version=mqtt.CONFIG_ENTRY_MINOR_VERSION,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    device = device_registry.async_get_device({("mqtt", "helloworld")})
    assert device is not None
    assert device.name == device_name

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.name == friendly_name

    assert (
        "MQTT device information always needs to include a name" in caplog.text
    ) is assert_log

    # Assert that no issues ware registered
    assert len(events) == 0
    await hass.async_block_till_done(wait_background_tasks=True)
    # Assert that no issues ware registered
    assert len(events) == 0