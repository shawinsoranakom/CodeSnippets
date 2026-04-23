async def test_discovery_works(
    hass: HomeAssistant, controller, upper_case_props, missing_csharp
) -> None:
    """Test a device being discovered."""
    device = setup_mock_accessory(controller)
    discovery_info = get_device_discovery_info(device, upper_case_props, missing_csharp)

    # Device is discovered
    result = await hass.config_entries.flow.async_init(
        "homekit_controller",
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=discovery_info,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pair"
    assert get_flow_context(hass, result) == {
        "source": config_entries.SOURCE_ZEROCONF,
        "title_placeholders": {"name": "TestDevice", "category": "Outlet"},
        "unique_id": "00:00:00:00:00:00",
    }

    # User initiates pairing - device enters pairing mode and displays code
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pair"

    # Pairing doesn't error error and pairing results
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"pairing_code": "111-22-333"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Koogeek-LS1-20833F"
    assert result["data"] == {}