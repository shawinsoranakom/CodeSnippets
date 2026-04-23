async def test_ssdp(hass: HomeAssistant, service) -> None:
    """Test ssdp step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location=SSDP_URL,
            upnp={
                ATTR_UPNP_MODEL_NUMBER: "RBR20",
                ATTR_UPNP_PRESENTATION_URL: URL,
                ATTR_UPNP_SERIAL: SERIAL,
            },
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: PASSWORD}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SERIAL
    assert result["title"] == TITLE
    assert result["data"].get(CONF_HOST) == HOST
    assert result["data"].get(CONF_PORT) == PORT_80
    assert result["data"].get(CONF_SSL) == SSL
    assert result["data"].get(CONF_USERNAME) == DEFAULT_USER
    assert result["data"][CONF_PASSWORD] == PASSWORD