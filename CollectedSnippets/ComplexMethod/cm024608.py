async def test_form_ssdp(
    hass: HomeAssistant, service: MagicMock, snapshot: SnapshotAssertion
) -> None:
    """Test we can setup from ssdp."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SsdpServiceInfo(
            ssdp_usn="mock_usn",
            ssdp_st="mock_st",
            ssdp_location="http://192.168.1.5:5000",
            upnp={
                ATTR_UPNP_FRIENDLY_NAME: "mydsm",
                ATTR_UPNP_SERIAL: "001132XXXX99",  # MAC address, but SSDP does not have `-`
            },
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.synology_dsm.config_flow.SynologyDSM",
        return_value=service,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_USERNAME: USERNAME, CONF_PASSWORD: PASSWORD}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SERIAL
    assert result["title"] == "mydsm"
    assert result["data"] == snapshot