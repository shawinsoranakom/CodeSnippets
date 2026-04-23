async def test_reauth_errors(
    hass: HomeAssistant,
    mock_config_flow_list_vehicles: AsyncMock,
    mock_async_setup_entry: AsyncMock,
    side_effect: BaseException,
    error: dict[str, str],
) -> None:
    """Test reauth flows that fail."""

    mock_config_flow_list_vehicles.side_effect = side_effect

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_CONFIG,
    )
    mock_entry.add_to_hass(hass)

    result1 = await mock_entry.start_reauth_flow(hass)

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"],
        TEST_CONFIG,
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == error

    # Complete the flow
    mock_config_flow_list_vehicles.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        TEST_CONFIG,
    )
    assert "errors" not in result3
    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"
    assert mock_entry.data == TEST_CONFIG
    assert len(mock_async_setup_entry.mock_calls) == 1