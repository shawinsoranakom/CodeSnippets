async def test_flow_discovered_devices_ignore_configured_manual_input(
    hass: HomeAssistant,
) -> None:
    """Test that config flow discovery ignores configured devices."""
    logging.getLogger("homeassistant.components.onvif").setLevel(logging.DEBUG)
    await setup_onvif_integration(hass)

    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with (
        patch(
            "homeassistant.components.onvif.config_flow.get_device"
        ) as mock_onvif_camera,
        patch(
            "homeassistant.components.onvif.config_flow.WSDiscovery"
        ) as mock_discovery,
        patch("homeassistant.components.onvif.ONVIFDevice") as mock_device,
    ):
        setup_mock_onvif_camera(mock_onvif_camera)
        setup_mock_discovery(mock_discovery, with_mac=True)
        setup_mock_device(mock_device)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"auto": True}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "device"
        assert len(result["data_schema"].schema[config_flow.CONF_HOST].container) == 2

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={config_flow.CONF_HOST: config_flow.CONF_MANUAL_INPUT},
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "configure"