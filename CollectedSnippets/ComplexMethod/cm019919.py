async def test_reconfigure_flow_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    mock_api: MagicMock,
) -> None:
    """Test the full reconfigure flow from start to finish without any exceptions."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert not result["errors"]
    assert "host" in result["data_schema"].schema
    # Form should have as default value the existing host
    host_key = next(k for k in result["data_schema"].schema if k.schema == "host")
    assert host_key.default() == mock_config_entry.data["host"]

    mock_api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    mock_api.async_get_name_and_mac = AsyncMock(
        return_value=(mock_config_entry.data["name"], mock_config_entry.data["mac"])
    )

    # Simulate user input with a new host
    new_host = "4.3.2.1"
    assert new_host != mock_config_entry.data["host"]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": new_host}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data["host"] == new_host
    assert len(mock_setup_entry.mock_calls) == 1