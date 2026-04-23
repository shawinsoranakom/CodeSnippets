async def test_flow_manual_entry_wrong_password(hass: HomeAssistant) -> None:
    """Test that we get a an auth error with the wrong password."""
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
        setup_mock_onvif_camera(mock_onvif_camera, two_profiles=True, auth_fail=True)
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
                    config_flow.CONF_PASSWORD: PASSWORD,
                },
            )

            await hass.async_block_till_done()
            assert len(mock_setup_entry.mock_calls) == 0

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "configure"
        assert result["errors"] == {"password": "auth_failed"}
        assert result["description_placeholders"] == {"error": "Authority failure"}
        setup_mock_onvif_camera(mock_onvif_camera, two_profiles=True)

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
                    config_flow.CONF_PASSWORD: PASSWORD,
                },
            )

            await hass.async_block_till_done()
            assert len(mock_setup_entry.mock_calls) == 1

        assert result["title"] == f"{NAME} - {MAC}"
        assert result["data"] == {
            config_flow.CONF_NAME: NAME,
            config_flow.CONF_HOST: HOST,
            config_flow.CONF_PORT: PORT,
            config_flow.CONF_USERNAME: USERNAME,
            config_flow.CONF_PASSWORD: PASSWORD,
        }