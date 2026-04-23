async def test_arming_exceptions(
    hass: HomeAssistant,
    mock_client: AsyncMock,
    mock_partition: AsyncMock,
    mock_location: AsyncMock,
    mock_config_entry: MockConfigEntry,
    service: str,
    prefix: str,
    exception: Exception,
    suffix: str,
    flows: int,
) -> None:
    """Test arming method exceptions."""
    await setup_integration(hass, mock_config_entry)

    entity_id = "alarm_control_panel.test"
    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED
    assert mock_location.get_panel_meta_data.call_count == 1

    mock_partition.arm.side_effect = exception

    mock_partition.arming_state = ArmingState.ARMING

    with pytest.raises(HomeAssistantError) as exc:
        await hass.services.async_call(
            ALARM_CONTROL_PANEL_DOMAIN,
            service,
            {ATTR_ENTITY_ID: entity_id, ATTR_CODE: CODE},
            blocking=True,
        )
    assert mock_partition.arm.call_count == 1

    assert exc.value.translation_key == f"{prefix}_{suffix}"

    assert hass.states.get(entity_id).state == AlarmControlPanelState.DISARMED
    assert mock_location.get_panel_meta_data.call_count == 1

    assert len(hass.config_entries.flow.async_progress_by_handler(DOMAIN)) == flows