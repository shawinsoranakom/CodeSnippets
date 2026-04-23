async def test_form_ssdp(hass: HomeAssistant) -> None:
    """Test we get the form with ssdp source."""

    with patch(
        "homeassistant.components.harmony.config_flow.HubConnector.get_remote_id",
        return_value=1234,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=SsdpServiceInfo(
                ssdp_usn="mock_usn",
                ssdp_st="mock_st",
                ssdp_location="http://192.168.1.12:8088/description",
                upnp={
                    "friendlyName": "Harmony Hub",
                },
            ),
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"
    assert result["errors"] == {}
    assert result["description_placeholders"] == {
        "host": "Harmony Hub",
        "name": "192.168.1.12",
    }
    progress = hass.config_entries.flow.async_progress()
    assert len(progress) == 1
    assert progress[0]["flow_id"] == result["flow_id"]
    assert progress[0]["context"]["confirm_only"] is True

    harmonyapi = _get_mock_harmonyapi(connect=True)

    with (
        patch(
            "homeassistant.components.harmony.util.HarmonyAPI",
            return_value=harmonyapi,
        ),
        patch(
            "homeassistant.components.harmony.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Harmony Hub"
    assert result2["data"] == {"host": "192.168.1.12", "name": "Harmony Hub"}
    assert len(mock_setup_entry.mock_calls) == 1