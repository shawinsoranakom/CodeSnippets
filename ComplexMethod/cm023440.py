async def test_setup_and_update(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    config_entry: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test sensor setup and update."""

    entry = entity_registry.async_get("device_tracker.10_10_10_10")
    assert entry
    assert entry.disabled
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    # Verify that the device_tracker and binary_sensor entities are linked to the same device
    binary_sensor = entity_registry.async_get("binary_sensor.10_10_10_10")
    assert entry.device_id == binary_sensor.device_id

    # check device tracker state is not there
    state = hass.states.get("device_tracker.10_10_10_10")
    assert state is None

    # enable the entity
    updated_entry = entity_registry.async_update_entity(
        entity_id="device_tracker.10_10_10_10", disabled_by=None
    )
    assert updated_entry != entry
    assert updated_entry.disabled is False

    # reload config entry to enable entity
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("device_tracker.10_10_10_10")
    assert state.state == "home"

    with patch(
        "homeassistant.components.ping.helpers.async_ping",
        return_value=Host(address="10.10.10.10", packets_sent=10, rtts=[]),
    ):
        # we need to travel two times into the future to run the update twice
        freezer.tick(timedelta(minutes=1, seconds=10))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

        freezer.tick(timedelta(minutes=4, seconds=10))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    assert (state := hass.states.get("device_tracker.10_10_10_10"))
    assert state.state == "not_home"

    freezer.tick(timedelta(minutes=1, seconds=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get("device_tracker.10_10_10_10"))
    assert state.state == "home"