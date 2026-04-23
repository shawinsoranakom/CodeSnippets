async def test_rssi_sensor(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test LIFX RSSI sensor entity."""

    config_entry = MockConfigEntry(
        domain=lifx.DOMAIN,
        title=DEFAULT_ENTRY_TITLE,
        data={CONF_HOST: IP_ADDRESS},
        unique_id=SERIAL,
    )
    config_entry.add_to_hass(hass)
    bulb = _mocked_bulb()
    with (
        _patch_discovery(device=bulb),
        _patch_config_flow_try_connect(device=bulb),
        _patch_device(device=bulb),
    ):
        await async_setup_component(hass, lifx.DOMAIN, {lifx.DOMAIN: {}})
        await hass.async_block_till_done()

    entity_id = "sensor.my_bulb_rssi"
    assert not hass.states.get(entity_id)

    entry = entity_registry.entities.get(entity_id)
    assert entry
    assert entry.disabled
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    # Test enabling entity, this will trigger a reload of the config entry
    updated_entry = entity_registry.async_update_entity(
        entry.entity_id, disabled_by=None
    )

    assert updated_entry != entry
    assert updated_entry.disabled is False
    assert updated_entry.unit_of_measurement == SIGNAL_STRENGTH_DECIBELS_MILLIWATT

    with (
        _patch_discovery(device=bulb),
        _patch_config_flow_try_connect(device=bulb),
        _patch_device(device=bulb),
    ):
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=120))
        await hass.async_block_till_done()

    rssi = hass.states.get(entity_id)
    assert (
        rssi.attributes[ATTR_UNIT_OF_MEASUREMENT] == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    )
    assert rssi.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.SIGNAL_STRENGTH
    assert rssi.attributes["state_class"] == SensorStateClass.MEASUREMENT