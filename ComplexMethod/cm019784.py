async def test_form_nondefault_pin_invalid(
    hass: HomeAssistant,
    friendly_name_error: Exception,
    result_error: str,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test we get the proper errors when trying to validate an user-provided PIN."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_friendly_name",
        side_effect=InvalidPinError,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 80},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "device_config"
    assert result2["errors"] is None

    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_friendly_name",
        side_effect=friendly_name_error,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_PIN: "4321"},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.FORM
    assert result2["step_id"] == "device_config"
    assert result3["errors"] == {"base": result_error}

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        {CONF_PIN: "4321"},
    )
    await hass.async_block_till_done()

    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["title"] == "Name of the device"
    assert result4["data"] == {
        CONF_WEBFSAPI_URL: "http://1.1.1.1:80/webfsapi",
        CONF_PIN: "4321",
    }
    mock_setup_entry.assert_called_once()