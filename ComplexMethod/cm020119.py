async def test_reconfigure_keyfile_upload(hass: HomeAssistant, knx_setup) -> None:
    """Test reconfigure flow uploading a keyfile for the first time."""
    start_data = {
        **DEFAULT_ENTRY_DATA,
        CONF_KNX_CONNECTION_TYPE: CONF_KNX_TUNNELING_TCP,
        CONF_HOST: "192.168.0.1",
        CONF_PORT: 3675,
        CONF_KNX_INDIVIDUAL_ADDRESS: "0.0.240",
        CONF_KNX_ROUTE_BACK: False,
        CONF_KNX_LOCAL_IP: None,
    }
    mock_config_entry = MockConfigEntry(
        title="KNX",
        domain="knx",
        data=start_data,
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    knx_setup.reset_mock()
    menu_step = await mock_config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        menu_step["flow_id"],
        {"next_step_id": "secure_knxkeys"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "secure_knxkeys"

    with patch_file_upload():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_KEYRING_FILE: FIXTURE_UPLOAD_UUID,
                CONF_KNX_KNXKEY_PASSWORD: "password",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "knxkeys_tunnel_select"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_KNX_TUNNEL_ENDPOINT_IA: "1.0.1",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data == {
        **start_data,
        CONF_KNX_KNXKEY_FILENAME: "knx/keyring.knxkeys",
        CONF_KNX_KNXKEY_PASSWORD: "password",
        CONF_KNX_TUNNEL_ENDPOINT_IA: "1.0.1",
        CONF_KNX_SECURE_USER_ID: None,
        CONF_KNX_SECURE_USER_PASSWORD: None,
        CONF_KNX_SECURE_DEVICE_AUTHENTICATION: None,
        CONF_KNX_ROUTING_BACKBONE_KEY: None,
        CONF_KNX_ROUTING_SYNC_LATENCY_TOLERANCE: None,
    }
    knx_setup.assert_called_once()