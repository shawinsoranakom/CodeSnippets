async def test_user_flow_selected(hass: HomeAssistant, ssdp_scanner_mock: Mock) -> None:
    """Test user-init'd flow, user selects discovered device."""
    ssdp_scanner_mock.async_get_discovery_info_by_st.side_effect = [
        [MOCK_DISCOVERY],
        [],
        [],
    ]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: MOCK_DEVICE_NAME}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_DEVICE_NAME
    assert result["data"] == {
        CONF_URL: MOCK_DEVICE_LOCATION,
        CONF_DEVICE_ID: MOCK_DEVICE_UDN,
        CONF_TYPE: MOCK_DEVICE_TYPE,
        CONF_MAC: MOCK_MAC_ADDRESS,
    }
    assert result["options"] == {}