async def test_abort_discovery_flow_with_user_flow(hass: HomeAssistant) -> None:
    """Test abort discovery flow if user flow is already in progress."""
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
        ),
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

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        assert len(hass.config_entries.flow.async_progress(DOMAIN)) == 2
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: TEST_HOST}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "link"

        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] is FlowResultType.CREATE_ENTRY

        # Verify the discovery flow was aborted
        assert not hass.config_entries.flow.async_progress(DOMAIN)