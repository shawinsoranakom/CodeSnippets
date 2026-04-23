async def test_external_update(
    hass: HomeAssistant,
    music_assistant_client: MagicMock,
) -> None:
    """Test external value update."""
    mass_player_id = "00:00:00:00:00:01"
    mass_option_key = "enhancer"
    entity_id = "switch.test_player_1_enhancer"

    await setup_integration_from_fixtures(hass, music_assistant_client)

    # get current option and remove it
    switch_option = next(
        option
        for option in music_assistant_client.players._players[mass_player_id].options
        if option.key == mass_option_key
    )
    music_assistant_client.players._players[mass_player_id].options.remove(
        switch_option
    )

    # set new value different from previous one
    previous_value = switch_option.value
    assert isinstance(previous_value, bool)
    switch_option.value = not previous_value
    music_assistant_client.players._players[mass_player_id].options.append(
        switch_option
    )

    # verify old HA state before trigger
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    await trigger_subscription_callback(
        hass, music_assistant_client, EventType.PLAYER_OPTIONS_UPDATED, mass_player_id
    )

    # verify new HA state after trigger
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON