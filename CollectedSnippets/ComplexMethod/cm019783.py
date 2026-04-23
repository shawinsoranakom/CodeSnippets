async def test_form_nondefault_pin(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    radio_id_return_value: str | None,
    radio_id_side_effect: Exception | None,
) -> None:
    """Test we get the form."""
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
        "homeassistant.components.frontier_silicon.config_flow.AFSAPI.get_radio_id",
        return_value=radio_id_return_value,
        side_effect=radio_id_side_effect,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_PIN: "4321"},
        )
    await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Name of the device"
    assert result3["data"] == {
        CONF_WEBFSAPI_URL: "http://1.1.1.1:80/webfsapi",
        CONF_PIN: "4321",
    }
    mock_setup_entry.assert_called_once()