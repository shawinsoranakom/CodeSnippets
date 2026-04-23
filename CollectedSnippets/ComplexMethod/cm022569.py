async def test_discovery_duplicate_filtered(
    hass: HomeAssistant,
    mock_discovery: MagicMock,
    mock_config_entry: MockConfigEntry,
    mock_gateway: MagicMock,
) -> None:
    """Test that already configured gateways are filtered out."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "select_gateway"
    errors = result.get("errors")
    assert errors is not None
    assert errors["base"] == "no_devices_found"

    await hass.config_entries.async_remove(mock_config_entry.entry_id)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "select_gateway"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"selected_gateway": mock_gateway.gw_sn},
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY