async def test_user_flow_undiscovered_manual(hass: HomeAssistant) -> None:
    """Test user-init'd flow, no discovered devices, user entering a valid URL."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "manual"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_URL: MOCK_DEVICE_LOCATION}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_DEVICE_NAME
    assert result["data"] == {
        CONF_URL: MOCK_DEVICE_LOCATION,
        CONF_DEVICE_ID: MOCK_DEVICE_UDN,
        CONF_TYPE: MOCK_DEVICE_TYPE,
        CONF_MAC: MOCK_MAC_ADDRESS,
    }
    assert result["options"] == {CONF_POLL_AVAILABILITY: True}