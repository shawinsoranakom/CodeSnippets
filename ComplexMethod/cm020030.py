async def test_config_flow_manual_host_no_serial_double_config(
    hass: HomeAssistant,
) -> None:
    """Failed flow manually initialized by the user twice.

    Host specified and an error getting the serial number.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.denonavr.receiver.DenonAVR.serial_number",
        None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_MODEL: TEST_MODEL,
        CONF_TYPE: TEST_RECEIVER_TYPE,
        CONF_MANUFACTURER: TEST_MANUFACTURER,
        CONF_SERIAL_NUMBER: None,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.denonavr.receiver.DenonAVR.serial_number",
        None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: TEST_HOST},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"