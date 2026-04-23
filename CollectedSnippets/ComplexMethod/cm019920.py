async def test_reconfigure_flow_cannot_connect(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    mock_api: MagicMock,
) -> None:
    """Test reconfigure flow with CannotConnect exception."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_api.async_generate_cert_if_missing = AsyncMock(return_value=True)
    mock_api.async_get_name_and_mac = AsyncMock(
        side_effect=[
            CannotConnect(),
            (mock_config_entry.data["name"], mock_config_entry.data["mac"]),
        ]
    )

    new_host = "4.3.2.1"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": new_host}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": "cannot_connect"}
    assert mock_config_entry.data["host"] == "1.2.3.4"
    assert len(mock_setup_entry.mock_calls) == 0

    # End in CREATE_ENTRY to test that its able to recover
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"host": new_host}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data["host"] == new_host
    assert len(mock_setup_entry.mock_calls) == 1