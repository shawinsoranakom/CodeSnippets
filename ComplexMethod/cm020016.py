async def test_form_reauth(hass: HomeAssistant) -> None:
    """Test reauthenticate."""
    entry, _, _ = await setup_onvif_integration(hass)

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert (
        _get_schema_default(result["data_schema"].schema, CONF_USERNAME)
        == entry.data[CONF_USERNAME]
    )

    with (
        patch(
            "homeassistant.components.onvif.config_flow.get_device"
        ) as mock_onvif_camera,
        patch("homeassistant.components.onvif.ONVIFDevice") as mock_device,
        patch(
            "homeassistant.components.onvif.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        setup_mock_onvif_camera(mock_onvif_camera, auth_failure=True)
        setup_mock_device(mock_device)

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                config_flow.CONF_USERNAME: "new-test-username",
                config_flow.CONF_PASSWORD: "new-test-password",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "reauth_confirm"
    assert result2["errors"] == {config_flow.CONF_PASSWORD: "auth_failed"}
    assert result2["description_placeholders"] == {
        CONF_NAME: "Mock Title",
        "error": "not authorized (subcodes:NotAuthorized)",
    }

    with (
        patch(
            "homeassistant.components.onvif.config_flow.get_device"
        ) as mock_onvif_camera,
        patch("homeassistant.components.onvif.ONVIFDevice") as mock_device,
        patch(
            "homeassistant.components.onvif.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        setup_mock_onvif_camera(mock_onvif_camera)
        setup_mock_device(mock_device)

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                config_flow.CONF_USERNAME: "new-test-username",
                config_flow.CONF_PASSWORD: "new-test-password",
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"
    assert len(mock_setup_entry.mock_calls) == 1
    assert entry.data[config_flow.CONF_USERNAME] == "new-test-username"
    assert entry.data[config_flow.CONF_PASSWORD] == "new-test-password"