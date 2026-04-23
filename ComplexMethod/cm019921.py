async def test_reconfigure_flow_unique_id_mismatch(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    mock_api: MagicMock,
) -> None:
    """Test reconfigure flow with a different device (unique_id mismatch)."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    # The new host corresponds to a device with a different MAC/unique_id
    new_mac = "FF:EE:DD:CC:BB:AA"
    assert new_mac != mock_config_entry.data["mac"]
    mock_api.async_get_name_and_mac = AsyncMock(return_value=("name", new_mac))

    new_host = "4.3.2.1"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": new_host}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unique_id_mismatch"
    assert mock_config_entry.data["host"] == "1.2.3.4"
    assert len(mock_setup_entry.mock_calls) == 0