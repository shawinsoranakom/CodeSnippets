async def test_user_flow_aborts_when_another_flow_finishes_while_in_progress(
    hass: HomeAssistant,
    mock_discovery: AsyncMock,
) -> None:
    """Test that user flow aborts when another flow finishes and creates a config entry."""
    # Mock zeroconf discovery
    mock_discovery.return_value = [MOCK_HTTP_ZEROCONF_SERVICE_INFO]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Check device list
    schema = result["data_schema"].schema
    device_selector = schema[CONF_DEVICE]
    options = {opt["value"]: opt["label"] for opt in device_selector.config["options"]}

    assert "AABBCCDDEEFF" in options
    assert options["AABBCCDDEEFF"] == "shellyplus2pm-AABBCCDDEEFF"

    # Now simulate another flow configuring the device while user is on the selection form
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AABBCCDDEEFF",
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 80},
    )
    entry.add_to_hass(hass)

    # User selects the device - should abort because it's now configured
    with patch(
        "homeassistant.components.shelly.config_flow.get_info",
        return_value={
            "mac": "AABBCCDDEEFF",
            "model": MODEL_PLUS_2PM,
            "auth": False,
            "gen": 2,
            "port": 80,
        },
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DEVICE: "AABBCCDDEEFF"},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"