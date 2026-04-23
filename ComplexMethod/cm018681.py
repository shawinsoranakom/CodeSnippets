async def test_discovery_not_setup(
    hass: HomeAssistant,
) -> None:
    """Handle the config flow and make sure it succeeds."""
    with (
        patch("homeassistant.components.roborock.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DHCP},
            data=DhcpServiceInfo(
                ip=NETWORK_INFO.ip,
                macaddress=NETWORK_INFO.mac.replace(":", ""),
                hostname="roborock-vacuum-a72",
            ),
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        with patch(
            "homeassistant.components.roborock.config_flow.RoborockApiClient.request_code_v4"
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_USERNAME: USER_EMAIL}
            )

            assert result["type"] is FlowResultType.FORM
            assert result["step_id"] == "code"
            assert result["errors"] == {}
        with patch(
            "homeassistant.components.roborock.config_flow.RoborockApiClient.code_login_v4",
            return_value=USER_DATA,
        ):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input={CONF_ENTRY_CODE: "123456"}
            )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["context"]["unique_id"] == ROBOROCK_RRUID
    assert result["title"] == USER_EMAIL
    assert result["data"] == MOCK_CONFIG
    assert result["result"]