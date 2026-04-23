async def test_light_attributes_state_update(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_homeworks: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test Homeworks light state changes."""
    entity_id = "light.foyer_sconces"
    mock_controller = MagicMock()
    mock_homeworks.return_value = mock_controller

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    mock_homeworks.assert_called_once_with("192.168.0.1", 1234, ANY, None, None)
    hw_callback = mock_homeworks.mock_calls[0][1][2]

    assert len(mock_controller.request_dimmer_level.mock_calls) == 1
    assert mock_controller.request_dimmer_level.mock_calls[0][1] == ("[02:08:01:01]",)

    assert hass.states.async_entity_ids("light") == unordered([entity_id])

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
    assert state == snapshot

    hw_callback(HW_LIGHT_CHANGED, ["[02:08:01:01]", 50])
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state == snapshot