async def test_dhcp_connection_error(hass: HomeAssistant) -> None:
    """Test DHCP connection to host error."""

    with patch(
        "homeassistant.components.airzone.AirzoneLocalApi.get_version",
        return_value=HVAC_VERSION_MOCK,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            data=DHCP_SERVICE_INFO,
            context={"source": config_entries.SOURCE_DHCP},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovered_connection"

    with patch(
        "homeassistant.components.airzone.AirzoneLocalApi.validate",
        side_effect=AirzoneError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PORT: 3001,
            },
        )

        assert result["errors"] == {"base": "cannot_connect"}

    with (
        patch(
            "homeassistant.components.airzone.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_dhw",
            return_value=HVAC_DHW_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac",
            return_value=HVAC_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac_systems",
            side_effect=SystemOutOfRange,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_version",
            return_value=HVAC_VERSION_MOCK,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_webserver",
            return_value=HVAC_WEBSERVER_MOCK,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PORT: TEST_PORT,
            },
        )

        await hass.async_block_till_done()

        conf_entries = hass.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        assert entry.state is ConfigEntryState.LOADED

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == f"Airzone {short_mac(HVAC_WEBSERVER_MOCK[API_MAC])}"
        assert result["data"][CONF_HOST] == TEST_IP
        assert result["data"][CONF_PORT] == TEST_PORT

        mock_setup_entry.assert_called_once()