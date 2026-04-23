async def test_ssdp_port_5555(hass: HomeAssistant, service) -> None:
    """Test ssdp step with port 5555."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location=SSDP_URL_SLL,
            upnp={
                ATTR_UPNP_MODEL_NUMBER: MODELS_PORT_5555[0],
                ATTR_UPNP_PRESENTATION_URL: URL_SSL,
                ATTR_UPNP_SERIAL: SERIAL,
            },
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    service.return_value.port = 5555
    service.return_value.ssl = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: PASSWORD}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SERIAL
    assert result["title"] == TITLE
    assert result["data"].get(CONF_HOST) == HOST
    assert result["data"].get(CONF_PORT) == PORT_5555
    assert result["data"].get(CONF_SSL) is True
    assert result["data"].get(CONF_USERNAME) == DEFAULT_USER
    assert result["data"][CONF_PASSWORD] == PASSWORD