async def test_option_flow_allow_service_calls(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_generic_device_entry: MockGenericDeviceEntryType,
) -> None:
    """Test config flow options for allow service calls."""
    entry = await mock_generic_device_entry(
        mock_client=mock_client,
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["data_schema"]({}) == {
        CONF_ALLOW_SERVICE_CALLS: DEFAULT_NEW_CONFIG_ALLOW_ALLOW_SERVICE_CALLS,
        CONF_SUBSCRIBE_LOGS: False,
    }

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["data_schema"]({}) == {
        CONF_ALLOW_SERVICE_CALLS: DEFAULT_NEW_CONFIG_ALLOW_ALLOW_SERVICE_CALLS,
        CONF_SUBSCRIBE_LOGS: False,
    }
    with patch(
        "homeassistant.components.esphome.async_setup_entry", return_value=True
    ) as mock_reload:
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_ALLOW_SERVICE_CALLS: True, CONF_SUBSCRIBE_LOGS: False},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_ALLOW_SERVICE_CALLS: True,
        CONF_SUBSCRIBE_LOGS: False,
    }
    assert len(mock_reload.mock_calls) == 1