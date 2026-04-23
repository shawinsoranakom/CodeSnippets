async def test_light_turn_on_and_off(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_hub_ping: AsyncMock,
    mock_hub_configuration_prod_awning_dimmer: AsyncMock,
    mock_hub_status_prod_dimmer: AsyncMock,
    mock_action_call: AsyncMock,
) -> None:
    """Test that a light entity is turned on and off correctly."""
    assert await setup_config_entry(hass, mock_config_entry)
    assert len(mock_hub_ping.mock_calls) == 1
    assert len(mock_hub_configuration_prod_awning_dimmer.mock_calls) == 1
    assert len(mock_hub_status_prod_dimmer.mock_calls) >= 1

    entity = hass.states.get("light.licht")
    assert entity is not None
    assert entity.state == STATE_OFF
    assert entity.attributes[ATTR_BRIGHTNESS] is None

    with patch(
        "wmspro.destination.Destination.refresh",
        return_value=True,
    ):
        before = len(mock_hub_status_prod_dimmer.mock_calls)

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity.entity_id},
            blocking=True,
        )

        entity = hass.states.get("light.licht")
        assert entity is not None
        assert entity.state == STATE_ON
        assert entity.attributes[ATTR_BRIGHTNESS] >= 1
        assert len(mock_hub_status_prod_dimmer.mock_calls) == before

    with patch(
        "wmspro.destination.Destination.refresh",
        return_value=True,
    ):
        before = len(mock_hub_status_prod_dimmer.mock_calls)

        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity.entity_id},
            blocking=True,
        )

        entity = hass.states.get("light.licht")
        assert entity is not None
        assert entity.state == STATE_OFF
        assert entity.attributes[ATTR_BRIGHTNESS] is None
        assert len(mock_hub_status_prod_dimmer.mock_calls) == before