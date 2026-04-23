async def test_config_flow_manual_discover_1_success(hass: HomeAssistant) -> None:
    """Successful flow manually initialized by the user.

    Without the host specified and 1 receiver discovered.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.denonavr.config_flow.denonavr.async_discover",
        return_value=TEST_DISCOVER_1_RECEIVER,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_NAME
    assert result["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_MODEL: TEST_MODEL,
        CONF_TYPE: TEST_RECEIVER_TYPE,
        CONF_MANUFACTURER: TEST_MANUFACTURER,
        CONF_SERIAL_NUMBER: TEST_SERIALNUMBER,
    }
    assert result["options"] == {CONF_USE_TELNET: True}