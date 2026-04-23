async def test_dhcp_flow(hass: HomeAssistant) -> None:
    """Test that DHCP discovery works."""

    with (
        patch(VALIDATE_AUTH_PATCH, return_value=MockPyObihai()),
        patch("homeassistant.components.obihai.config_flow.gethostbyname"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DHCP_SERVICE_INFO,
            context={"source": config_entries.SOURCE_DHCP},
        )

        flows = hass.config_entries.flow.async_progress()
        assert result["type"] is FlowResultType.FORM
        assert len(flows) == 1
        assert (
            get_schema_suggestion(result["data_schema"].schema, CONF_USERNAME)
            == USER_INPUT[CONF_USERNAME]
        )
        assert (
            get_schema_suggestion(result["data_schema"].schema, CONF_PASSWORD)
            == USER_INPUT[CONF_PASSWORD]
        )
        assert (
            get_schema_suggestion(result["data_schema"].schema, CONF_HOST)
            == DHCP_SERVICE_INFO.ip
        )
        assert flows[0].get("context", {}).get("source") == config_entries.SOURCE_DHCP

        # Verify we get dropped into the normal user flow with non-default credentials
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=USER_INPUT
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY