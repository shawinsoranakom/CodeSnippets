async def test_spa_preset_modes(
    hass: HomeAssistant, client: MagicMock, integration: MockConfigEntry
) -> None:
    """Test the various preset modes."""
    state = hass.states.get(ENTITY_CLIMATE)
    assert state
    modes = state.attributes.get(ATTR_PRESET_MODES)
    assert modes == ["ready", "rest"]

    # Put it in Ready and Rest
    modelist = ["ready", "rest"]
    for mode in modelist:
        client.heat_mode.state = HeatMode[mode.upper()]
        await common.async_set_preset_mode(hass, mode, ENTITY_CLIMATE)

        state = await client_update(hass, client, ENTITY_CLIMATE)
        assert state
        assert state.attributes[ATTR_PRESET_MODE] == mode

    with pytest.raises(ServiceValidationError):
        await common.async_set_preset_mode(hass, 2, ENTITY_CLIMATE)

    # put it in RNR and test assertion
    client.heat_mode.state = HeatMode.READY_IN_REST
    state = await client_update(hass, client, ENTITY_CLIMATE)
    assert state
    assert state.attributes[ATTR_PRESET_MODE] == "ready_in_rest"