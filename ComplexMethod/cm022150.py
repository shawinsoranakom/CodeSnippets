async def test_update_data_error_handling(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that update data errors are handled and retried."""
    await setup_with_selected_platforms(hass, mock_config_entry, [Platform.CLIMATE])

    assert (state := hass.states.get(ENTITY_ID))
    assert state.attributes[ATTR_TEMPERATURE] == 20.0

    # Fail with TimeoutError (expected) and raise UpdateFailed after 3 retries
    with patch.object(
        mock_config_entry.runtime_data.device,
        "get_temperature_async",
        side_effect=TimeoutError(),
    ) as mock_get_temperature:
        await mock_config_entry.runtime_data.async_refresh()
        await hass.async_block_till_done()

        assert mock_get_temperature.call_count == 3
        assert mock_config_entry.runtime_data.last_update_success is False
        assert (state := hass.states.get(ENTITY_ID))
        assert state.attributes[ATTR_TEMPERATURE] == 20.0

    # Fail with OSError (unexpected) and raise UpdateFailed directly
    with patch.object(
        mock_config_entry.runtime_data.device,
        "get_temperature_async",
        side_effect=OSError(),
    ) as mock_get_temperature:
        await mock_config_entry.runtime_data.async_refresh()
        await hass.async_block_till_done()

        assert mock_get_temperature.call_count == 1
        assert mock_config_entry.runtime_data.last_update_success is False
        assert (state := hass.states.get(ENTITY_ID))
        assert state.attributes[ATTR_TEMPERATURE] == 20.0

    # Fail once with TimeoutError and then succeed, verify that data is updated
    updated_temperatures = dict(mock_config_entry.runtime_data.data.temperatures)
    updated_temperatures["manualTemp"] = 27.0

    with patch.object(
        mock_config_entry.runtime_data.device,
        "get_temperature_async",
        side_effect=[TimeoutError(), updated_temperatures],
    ) as mock_get_temperature:
        await mock_config_entry.runtime_data.async_refresh()
        await hass.async_block_till_done()

        assert mock_get_temperature.call_count == 2
        assert mock_config_entry.runtime_data.last_update_success is True
        assert (state := hass.states.get(ENTITY_ID))
        assert state.attributes[ATTR_TEMPERATURE] == 27.0