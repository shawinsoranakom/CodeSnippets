async def test_number_entities(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mock_homewizardenergy: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test number handles state changes correctly."""
    assert (state := hass.states.get("number.device_status_light_brightness"))
    assert snapshot == state

    assert (entity_entry := entity_registry.async_get(state.entity_id))
    assert snapshot == entity_entry

    assert entity_entry.device_id
    assert (device_entry := device_registry.async_get(entity_entry.device_id))
    assert snapshot == device_entry

    # Test unknown handling
    assert state.state == "100"

    mock_homewizardenergy.combined.return_value = CombinedModels(
        device=None, measurement=Measurement(), system=System(), state=State()
    )

    async_fire_time_changed(hass, dt_util.utcnow() + UPDATE_INTERVAL)
    await hass.async_block_till_done()

    assert (state := hass.states.get(state.entity_id))
    assert state.state == STATE_UNKNOWN

    # Test service methods
    assert len(mock_homewizardenergy.state.mock_calls) == 0
    await hass.services.async_call(
        number.DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: state.entity_id,
            ATTR_VALUE: 50,
        },
        blocking=True,
    )

    assert len(mock_homewizardenergy.system.mock_calls) == 1
    mock_homewizardenergy.system.assert_called_with(status_led_brightness_pct=50)

    mock_homewizardenergy.system.side_effect = RequestError
    with pytest.raises(
        HomeAssistantError,
        match=r"^An error occurred while communicating with your HomeWizard device$",
    ):
        await hass.services.async_call(
            number.DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: state.entity_id,
                ATTR_VALUE: 50,
            },
            blocking=True,
        )

    mock_homewizardenergy.system.side_effect = DisabledError
    with pytest.raises(
        HomeAssistantError,
        match=r"^The local API is disabled$",
    ):
        await hass.services.async_call(
            number.DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: state.entity_id,
                ATTR_VALUE: 50,
            },
            blocking=True,
        )