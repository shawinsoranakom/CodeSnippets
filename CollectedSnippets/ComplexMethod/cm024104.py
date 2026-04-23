async def test_reauth(
    hass: HomeAssistant,
    mock_config_flow_list_vehicles: AsyncMock,
    mock_async_setup_entry: AsyncMock,
) -> None:
    """Test reauth flow."""

    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data=TEST_CONFIG,
    )
    mock_entry.add_to_hass(hass)

    result1 = await mock_entry.start_reauth_flow(hass)

    assert result1["type"] is FlowResultType.FORM
    assert result1["step_id"] == "reauth_confirm"
    assert not result1["errors"]

    result2 = await hass.config_entries.flow.async_configure(
        result1["flow_id"],
        TEST_CONFIG,
    )
    await hass.async_block_till_done()
    assert len(mock_async_setup_entry.mock_calls) == 1
    assert len(mock_config_flow_list_vehicles.mock_calls) == 1

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert mock_entry.data == TEST_CONFIG