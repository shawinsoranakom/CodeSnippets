async def test_flow_manual_entry_updates_existing_user_password(
    hass: HomeAssistant,
) -> None:
    """Test that the existing username and password can be updated via manual entry."""
    entry, _, _ = await setup_onvif_integration(hass)

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
        setup_mock_onvif_camera(mock_onvif_camera, two_profiles=True)
        # no discovery
        mock_discovery.return_value = []
        setup_mock_device(mock_device)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"auto": False},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "configure"

        with patch(
            "homeassistant.components.onvif.async_setup_entry", return_value=True
        ) as mock_setup_entry:
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    config_flow.CONF_NAME: NAME,
                    config_flow.CONF_HOST: HOST,
                    config_flow.CONF_PORT: PORT,
                    config_flow.CONF_USERNAME: USERNAME,
                    config_flow.CONF_PASSWORD: "new_password",
                },
            )

            await hass.async_block_till_done()

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"
        assert entry.data[config_flow.CONF_USERNAME] == USERNAME
        assert entry.data[config_flow.CONF_PASSWORD] == "new_password"
        assert len(mock_setup_entry.mock_calls) == 1