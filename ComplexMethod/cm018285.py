async def test_form(hass: HomeAssistant) -> None:
    """Test that the form is served with valid input."""

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
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

        await hass.async_block_till_done()

        conf_entries = hass.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        assert entry.state is ConfigEntryState.LOADED

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == f"Airzone {CONFIG[CONF_HOST]}:{CONFIG[CONF_PORT]}"
        assert result["data"][CONF_HOST] == CONFIG[CONF_HOST]
        assert result["data"][CONF_PORT] == CONFIG[CONF_PORT]
        assert result["data"][CONF_ID] == CONFIG[CONF_ID]

        assert len(mock_setup_entry.mock_calls) == 1