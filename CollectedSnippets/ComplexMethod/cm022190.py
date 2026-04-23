async def test_update_listener(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_pyiss: MagicMock
) -> None:
    """Test options update triggers reload and applies new options."""
    state = hass.states.get("sensor.iss")
    assert state is not None
    assert "lat" in state.attributes
    assert "long" in state.attributes
    assert ATTR_LATITUDE not in state.attributes
    assert ATTR_LONGITUDE not in state.attributes

    hass.config_entries.async_update_entry(
        init_integration, options={CONF_SHOW_ON_MAP: True}
    )
    await hass.async_block_till_done()

    # After reload with show_on_map=True, attributes should switch
    state = hass.states.get("sensor.iss")
    assert state is not None
    assert ATTR_LATITUDE in state.attributes
    assert ATTR_LONGITUDE in state.attributes
    assert "lat" not in state.attributes
    assert "long" not in state.attributes