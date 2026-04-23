async def test_updates_from_groups_changed(
    hass: HomeAssistant, config_entry: MockConfigEntry, controller: MockHeos
) -> None:
    """Test player updates from changes to groups."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    # Assert current state
    state = hass.states.get("media_player.test_player")
    assert state is not None
    assert state.attributes[ATTR_GROUP_MEMBERS] == [
        "media_player.test_player",
        "media_player.test_player_2",
    ]
    state = hass.states.get("media_player.test_player_2")
    assert state is not None
    assert state.attributes[ATTR_GROUP_MEMBERS] == [
        "media_player.test_player",
        "media_player.test_player_2",
    ]

    # Clear group information
    controller.mock_set_groups({})
    for player in controller.players.values():
        player.group_id = None
    await controller.dispatcher.wait_send(
        SignalType.CONTROLLER_EVENT, const.EVENT_GROUPS_CHANGED, None
    )
    await hass.async_block_till_done()

    # Assert groups changed
    state = hass.states.get("media_player.test_player")
    assert state is not None
    assert state.attributes[ATTR_GROUP_MEMBERS] is None

    state = hass.states.get("media_player.test_player_2")
    assert state is not None
    assert state.attributes[ATTR_GROUP_MEMBERS] is None