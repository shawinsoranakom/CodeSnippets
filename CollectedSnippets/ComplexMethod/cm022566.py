async def test_discovery_no_gateways_found(
    hass: HomeAssistant,
    mock_discovery: MagicMock,
    mock_gateway: MagicMock,
) -> None:
    """Test discovery step when no gateways are found."""
    mock_discovery.discover_gateways.return_value = []

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "select_gateway"
    errors = result.get("errors")
    assert errors is not None
    assert errors["base"] == "no_devices_found"

    mock_discovery.discover_gateways.return_value = [mock_gateway]
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "select_gateway"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"selected_gateway": mock_gateway.gw_sn},
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY