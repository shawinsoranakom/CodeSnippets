async def test_reconfigure_token_error_then_recovery(
    hass: HomeAssistant,
    mock_growatt_v1_api: MagicMock,
    mock_config_entry: MockConfigEntry,
    plant_list_side_effect: Exception,
    expected_error: str,
) -> None:
    """Test token reconfigure shows error then allows recovery."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_growatt_v1_api.plant_list.side_effect = plant_list_side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], FIXTURE_USER_INPUT_TOKEN
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": expected_error}

    # Recover with a valid token
    mock_growatt_v1_api.plant_list.side_effect = None
    mock_growatt_v1_api.plant_list.return_value = GROWATT_V1_PLANT_LIST_RESPONSE
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], FIXTURE_USER_INPUT_TOKEN
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"