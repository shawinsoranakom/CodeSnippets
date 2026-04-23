async def test_invalid_device_url(
    hass: HomeAssistant,
    webfsapi_endpoint_error: Exception,
    result_error: str,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test flow when the user provides an invalid device IP/hostname."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_webfsapi_endpoint",
        side_effect=webfsapi_endpoint_error,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_PORT: 80},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "user"
    assert result2["errors"] == {"base": result_error}

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        {CONF_HOST: "1.1.1.1", CONF_PORT: 80},
    )
    await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Name of the device"
    assert result3["data"] == {
        CONF_WEBFSAPI_URL: "http://1.1.1.1:80/webfsapi",
        CONF_PIN: "1234",
    }
    mock_setup_entry.assert_called_once()