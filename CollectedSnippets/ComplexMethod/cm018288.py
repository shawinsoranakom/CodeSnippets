async def test_dhcp_invalid_system_id(hass: HomeAssistant) -> None:
    """Test Invalid System ID 0."""

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

    with (
        patch(
            "homeassistant.components.airzone.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_dhw",
            side_effect=HotWaterNotAvailable,
        ),
        patch(
            "homeassistant.components.airzone.AirzoneLocalApi.get_hvac",
            side_effect=InvalidSystem,
        ) as mock_hvac,
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
            side_effect=InvalidMethod,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PORT: TEST_PORT,
            },
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "discovered_connection"
        assert result["errors"] == {CONF_ID: "invalid_system_id"}

        mock_hvac.return_value = HVAC_MOCK[API_SYSTEMS][0]
        mock_hvac.side_effect = None

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PORT: TEST_PORT,
                CONF_ID: TEST_ID,
            },
        )

        await hass.async_block_till_done()

        conf_entries = hass.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        assert entry.state is ConfigEntryState.LOADED

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == f"Airzone {short_mac(DHCP_SERVICE_INFO.macaddress)}"
        assert result["data"][CONF_HOST] == TEST_IP
        assert result["data"][CONF_PORT] == TEST_PORT
        assert result["data"][CONF_ID] == TEST_ID

        mock_setup_entry.assert_called_once()