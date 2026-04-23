async def test_insights_multiple_doors(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test insights event with multiple doors dispatches events for each."""
    handlers = _get_ws_handlers(mock_client)

    insights_msg = InsightsAdd(
        event="access.logs.insights.add",
        data=InsightsAddData(
            event_type="access.door.unlock",
            result="ACCESS",
            metadata=InsightsMetadata(
                door=[
                    InsightsMetadataEntry(id="door-001", display_name="Front Door"),
                    InsightsMetadataEntry(id="door-002", display_name="Back Door"),
                ],
                actor=InsightsMetadataEntry(display_name="John Doe"),
                authentication=InsightsMetadataEntry(display_name="NFC"),
            ),
        ),
    )

    await handlers["access.logs.insights.add"](insights_msg)
    await hass.async_block_till_done()

    front_state = hass.states.get(FRONT_DOOR_ACCESS_ENTITY)
    assert front_state is not None
    assert front_state.attributes["event_type"] == "access_granted"
    assert front_state.attributes["actor"] == "John Doe"
    assert front_state.state == "2025-01-01T00:00:00.000+00:00"

    back_state = hass.states.get(BACK_DOOR_ACCESS_ENTITY)
    assert back_state is not None
    assert back_state.attributes["event_type"] == "access_granted"
    assert back_state.attributes["actor"] == "John Doe"
    assert back_state.state == "2025-01-01T00:00:00.000+00:00"