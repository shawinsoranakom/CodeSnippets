async def test_multiple_updates(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    client: AqualinkClient,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test all possible results of online status transition after update."""
    config_entry.add_to_hass(hass)

    system = get_aqualink_system(client, cls=IaquaSystem)
    system.online = True
    system.update = AsyncMock()
    systems = {system.serial: system}

    light = get_aqualink_device(
        system, name="aux_1", cls=IaquaLightSwitch, data={"state": "1"}
    )
    devices = {light.name: light}

    system.get_devices = AsyncMock(return_value=devices)

    with (
        patch(
            "homeassistant.components.iaqualink.AqualinkClient.login",
            return_value=None,
        ),
        patch(
            "homeassistant.components.iaqualink.AqualinkClient.get_systems",
            return_value=systems,
        ),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    entity_ids = hass.states.async_entity_ids(LIGHT_DOMAIN)
    assert len(entity_ids) == 1
    entity_id = entity_ids[0]

    def assert_state(expected_state: str) -> None:
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == expected_state

    def set_online_to_true():
        system.online = True

    def set_online_to_false():
        system.online = False

    async def fail_update() -> None:
        system.online = None
        raise AqualinkServiceException

    system.update = AsyncMock()

    # True -> True
    system.online = True
    system.update.side_effect = set_online_to_true
    await _advance_coordinator_time(hass, freezer)
    assert system.update.await_count == 1
    assert_state(STATE_ON)

    # True -> False
    system.online = True
    system.update.side_effect = set_online_to_false
    await _advance_coordinator_time(hass, freezer)
    assert system.update.await_count == 2
    assert_state(STATE_UNAVAILABLE)

    # True -> None / ServiceException
    system.online = True
    system.update.side_effect = fail_update
    await _advance_coordinator_time(hass, freezer)
    assert system.update.await_count == 3
    assert_state(STATE_UNAVAILABLE)

    # False -> False
    system.online = False
    system.update.side_effect = set_online_to_false
    await _advance_coordinator_time(hass, freezer)
    assert system.update.await_count == 4
    assert_state(STATE_UNAVAILABLE)

    # False -> True
    system.online = False
    system.update.side_effect = set_online_to_true
    await _advance_coordinator_time(hass, freezer)
    assert system.update.await_count == 5
    assert_state(STATE_ON)

    # False -> None / ServiceException
    system.online = False
    system.update.side_effect = fail_update
    await _advance_coordinator_time(hass, freezer)
    assert system.update.await_count == 6
    assert_state(STATE_UNAVAILABLE)

    # None -> None / ServiceException
    system.online = None
    system.update.side_effect = fail_update
    await _advance_coordinator_time(hass, freezer)
    assert system.update.await_count == 7
    assert_state(STATE_UNAVAILABLE)

    # None -> True
    system.online = None
    system.update.side_effect = set_online_to_true
    await _advance_coordinator_time(hass, freezer)
    assert system.update.await_count == 8
    assert_state(STATE_ON)

    # None -> False
    system.online = None
    system.update.side_effect = set_online_to_false
    await _advance_coordinator_time(hass, freezer)
    assert system.update.await_count == 9
    assert_state(STATE_UNAVAILABLE)

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.NOT_LOADED