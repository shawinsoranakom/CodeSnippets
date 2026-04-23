async def test_user_flow_with_zeroconf_devices(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
) -> None:
    """Test user flow shows discovered Zeroconf devices."""
    # Mock zeroconf discovery to return a device
    mock_discovery.return_value = [MOCK_HTTP_ZEROCONF_SERVICE_INFO]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Should show form with discovered device
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Check device is in the options
    schema = result["data_schema"].schema
    device_selector = schema[CONF_DEVICE]
    options = device_selector.config["options"]

    # Should have the discovered device plus manual entry
    # Options is now a list of dicts with 'value' and 'label' keys
    option_values = {opt["value"]: opt["label"] for opt in options}
    assert "AABBCCDDEEFF" in option_values  # MAC as value
    assert "manual" in option_values
    assert option_values["AABBCCDDEEFF"] == "shellyplus2pm-AABBCCDDEEFF"
    assert (
        option_values["manual"] == "manual"
    )  # Translation key, not the translated text

    # Select the discovered device and complete setup
    with (
        patch(
            "homeassistant.components.shelly.config_flow.get_info",
            return_value={
                "mac": "AABBCCDDEEFF",
                "model": MODEL_PLUS_2PM,
                "auth": False,
                "gen": 2,
                "port": 80,
            },
        ),
        patch(
            "homeassistant.components.shelly.config_flow.RpcDevice.create",
            return_value=create_mock_rpc_device("Test Zeroconf Device"),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE: "AABBCCDDEEFF"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "AABBCCDDEEFF"
    assert result["data"][CONF_HOST] == "192.168.1.100"