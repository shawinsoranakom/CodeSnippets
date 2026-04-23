async def test_coordinator_failure_refresh_and_stream(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
) -> None:
    """Test entity available state via coordinator refresh and event stream."""
    appliance_data = (
        cast(str, appliance.to_json())
        .replace("ha_id", "haId")
        .replace("e_number", "enumber")
    )
    entity_id_1 = "binary_sensor.washer_remote_control"
    entity_id_2 = "binary_sensor.washer_remote_start"
    await async_setup_component(hass, HA_DOMAIN, {})
    await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED
    state = hass.states.get(entity_id_1)
    assert state
    assert state.state != STATE_UNAVAILABLE
    state = hass.states.get(entity_id_2)
    assert state
    assert state.state != STATE_UNAVAILABLE

    client.get_specific_appliance.side_effect = HomeConnectError()

    # Force a coordinator refresh.
    await hass.services.async_call(
        HA_DOMAIN, SERVICE_UPDATE_ENTITY, {ATTR_ENTITY_ID: entity_id_1}, blocking=True
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id_1)
    assert state
    assert state.state == STATE_UNAVAILABLE
    state = hass.states.get(entity_id_2)
    assert state
    assert state.state == STATE_UNAVAILABLE

    # Test that the entity becomes available again after a successful update.

    client.get_specific_appliance.side_effect = None
    client.get_specific_appliance.return_value = HomeAppliance.from_json(appliance_data)

    # Move time forward to pass the debounce time.
    freezer.tick(timedelta(hours=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Force a coordinator refresh.
    await hass.services.async_call(
        HA_DOMAIN, SERVICE_UPDATE_ENTITY, {ATTR_ENTITY_ID: entity_id_1}, blocking=True
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id_1)
    assert state
    assert state.state != STATE_UNAVAILABLE
    state = hass.states.get(entity_id_2)
    assert state
    assert state.state != STATE_UNAVAILABLE

    # Test that the event stream makes the entity go available too.

    # First make the entity unavailable.
    client.get_specific_appliance.side_effect = HomeConnectError()

    # Move time forward to pass the debounce time
    freezer.tick(timedelta(hours=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Force a coordinator refresh
    await hass.services.async_call(
        HA_DOMAIN, SERVICE_UPDATE_ENTITY, {ATTR_ENTITY_ID: entity_id_1}, blocking=True
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id_1)
    assert state
    assert state.state == STATE_UNAVAILABLE
    state = hass.states.get(entity_id_2)
    assert state
    assert state.state == STATE_UNAVAILABLE

    # Now make the entity available again.
    client.get_specific_appliance.side_effect = None
    client.get_specific_appliance.return_value = HomeAppliance.from_json(appliance_data)

    # One event should make all entities for this appliance available again.
    event_message = EventMessage(
        appliance.ha_id,
        EventType.STATUS,
        ArrayOfEvents(
            [
                Event(
                    key=EventKey.BSH_COMMON_STATUS_REMOTE_CONTROL_ACTIVE,
                    raw_key=EventKey.BSH_COMMON_STATUS_REMOTE_CONTROL_ACTIVE.value,
                    timestamp=0,
                    level="",
                    handling="",
                    value=False,
                )
            ],
        ),
    )
    await client.add_events([event_message])
    await hass.async_block_till_done()

    state = hass.states.get(entity_id_1)
    assert state
    assert state.state != STATE_UNAVAILABLE
    state = hass.states.get(entity_id_2)
    assert state
    assert state.state != STATE_UNAVAILABLE