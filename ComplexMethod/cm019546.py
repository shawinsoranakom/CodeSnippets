async def test_cover_open_to_pos(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_hub_ping: AsyncMock,
    mock_hub_configuration: AsyncMock,
    mock_hub_status: AsyncMock,
    mock_action_call: AsyncMock,
    request: pytest.FixtureRequest,
    entity_name: str,
) -> None:
    """Test that a cover entity is opened to correct position."""
    mock_hub_configuration = request.getfixturevalue(mock_hub_configuration)
    mock_hub_status = request.getfixturevalue(mock_hub_status)

    assert await setup_config_entry(hass, mock_config_entry)
    assert len(mock_hub_ping.mock_calls) == 1
    assert len(mock_hub_configuration.mock_calls) == 1
    assert len(mock_hub_status.mock_calls) >= 1

    entity = hass.states.get(entity_name)
    assert entity is not None
    assert entity.state == STATE_CLOSED
    assert entity.attributes["current_position"] == 0

    with patch(
        "wmspro.destination.Destination.refresh",
        return_value=True,
    ):
        before = len(mock_hub_status.mock_calls)

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: entity.entity_id, "position": 50},
            blocking=True,
        )

        entity = hass.states.get(entity_name)
        assert entity is not None
        assert entity.state == STATE_OPEN
        assert entity.attributes["current_position"] == 50
        assert len(mock_hub_status.mock_calls) == before