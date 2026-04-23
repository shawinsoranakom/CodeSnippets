async def test_ssdp_discovery(hass: HomeAssistant) -> None:
    """Test SSDP discovery."""
    with (
        patch(
            "homeassistant.components.nanoleaf.config_flow.load_json_object",
            return_value={},
        ),
        patch(
            "homeassistant.components.nanoleaf.config_flow.Nanoleaf",
            return_value=_mock_nanoleaf(TEST_HOST, TEST_TOKEN),
        ),
        patch(
            "homeassistant.components.nanoleaf.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_SSDP},
            data=SsdpServiceInfo(
                ssdp_usn="mock_usn",
                ssdp_st="mock_st",
                upnp={},
                ssdp_headers={
                    "_host": TEST_HOST,
                    "nl-devicename": TEST_NAME,
                    "nl-deviceid": TEST_DEVICE_ID,
                },
            ),
        )

        assert result["type"] is FlowResultType.FORM
        assert result["errors"] is None
        assert result["step_id"] == "link"

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == TEST_NAME
    assert result2["data"] == {
        CONF_HOST: TEST_HOST,
        CONF_TOKEN: TEST_TOKEN,
    }

    assert len(mock_setup_entry.mock_calls) == 1