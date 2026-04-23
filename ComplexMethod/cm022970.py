async def test_speed_dynamically_handle_segments(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_wled: MagicMock,
    entity_id_segment0: str,
    entity_id_segment1: str,
    state_segment0: str,
    state_segment1: str,
) -> None:
    """Test if a new/deleted segment is dynamically added/removed."""
    assert (segment0 := hass.states.get(entity_id_segment0))
    assert segment0.state == state_segment0
    assert not hass.states.get(entity_id_segment1)

    # Test adding a segment dynamically...
    return_value = mock_wled.update.return_value
    mock_wled.update.return_value = WLEDDevice.from_dict(
        await async_load_json_object_fixture(hass, "rgb.json", DOMAIN)
    )

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (segment0 := hass.states.get(entity_id_segment0))
    assert segment0.state == state_segment0
    assert (segment1 := hass.states.get(entity_id_segment1))
    assert segment1.state == state_segment1

    # Test remove segment again...
    mock_wled.update.return_value = return_value
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (segment0 := hass.states.get(entity_id_segment0))
    assert segment0.state == state_segment0
    assert (segment1 := hass.states.get(entity_id_segment1))
    assert segment1.state == STATE_UNAVAILABLE