async def test_flow_discovered_devices(hass: HomeAssistant) -> None:
    """Test that config flow works for discovered devices."""
    logging.getLogger("homeassistant.components.onvif").setLevel(logging.DEBUG)

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
        setup_mock_discovery(mock_discovery)
        setup_mock_device(mock_device)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"auto": True}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "device"
        container = result["data_schema"].schema[config_flow.CONF_HOST].container
        assert len(container) == 3
        assert container == {
            "Manually configure ONVIF device": "Manually configure ONVIF device",
            "1.2.3.4": "urn:uuid:123456789 (1.2.3.4) [IPC model]",
            "5.6.7.8": "urn:uuid:987654321 (5.6.7.8)",
        }

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={config_flow.CONF_HOST: HOST}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "configure"

        with patch(
            "homeassistant.components.onvif.async_setup_entry", return_value=True
        ) as mock_setup_entry:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    config_flow.CONF_USERNAME: USERNAME,
                    config_flow.CONF_PASSWORD: PASSWORD,
                },
            )

            await hass.async_block_till_done()
            assert len(mock_setup_entry.mock_calls) == 1

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == f"{URN} - {MAC}"
        assert result["data"] == {
            config_flow.CONF_NAME: URN,
            config_flow.CONF_HOST: HOST,
            config_flow.CONF_PORT: PORT,
            config_flow.CONF_USERNAME: USERNAME,
            config_flow.CONF_PASSWORD: PASSWORD,
        }