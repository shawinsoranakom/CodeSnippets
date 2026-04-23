async def test_user_step_success(
    hass: HomeAssistant, mock_casper_glow: MagicMock
) -> None:
    """Test user step success path."""
    with patch(
        "homeassistant.components.casper_glow.config_flow.async_discovered_service_info",
        return_value=[NOT_CASPER_GLOW_DISCOVERY_INFO, CASPER_GLOW_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    # Inject before configure so async_setup_entry can find the device via
    # async_ble_device_from_address.
    inject_bluetooth_service_info(hass, CASPER_GLOW_DISCOVERY_INFO)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ADDRESS: CASPER_GLOW_DISCOVERY_INFO.address,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == human_readable_name(
        None, CASPER_GLOW_DISCOVERY_INFO.name, CASPER_GLOW_DISCOVERY_INFO.address
    )
    assert result["data"] == {
        CONF_ADDRESS: CASPER_GLOW_DISCOVERY_INFO.address,
    }
    assert result["result"].unique_id == format_mac(CASPER_GLOW_DISCOVERY_INFO.address)