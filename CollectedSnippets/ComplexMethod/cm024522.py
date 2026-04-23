async def test_switch_entities(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    mock_homewizardenergy: MagicMock,
    snapshot: SnapshotAssertion,
    entity_id: str,
    method: str,
    parameter: str,
) -> None:
    """Test that switch handles state changes correctly."""
    assert (state := hass.states.get(entity_id))
    assert snapshot == state

    assert (entity_entry := entity_registry.async_get(entity_id))
    assert snapshot == entity_entry

    assert entity_entry.device_id
    assert (device_entry := device_registry.async_get(entity_entry.device_id))
    assert snapshot == device_entry

    mocked_method = getattr(mock_homewizardenergy, method)

    # Turn power_on on
    await hass.services.async_call(
        switch.DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(mocked_method.mock_calls) == 1
    mocked_method.assert_called_with(**{parameter: True})

    # Turn power_on off
    await hass.services.async_call(
        switch.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(mocked_method.mock_calls) == 2
    mocked_method.assert_called_with(**{parameter: False})

    # Test request error handling
    mocked_method.side_effect = RequestError

    with pytest.raises(
        HomeAssistantError,
        match=r"^An error occurred while communicating with your HomeWizard device$",
    ):
        await hass.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    with pytest.raises(
        HomeAssistantError,
        match=r"^An error occurred while communicating with your HomeWizard device$",
    ):
        await hass.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    # Test disabled error handling
    mocked_method.side_effect = DisabledError

    with pytest.raises(
        HomeAssistantError,
        match=r"^The local API is disabled$",
    ):
        await hass.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    with pytest.raises(
        HomeAssistantError,
        match=r"^The local API is disabled$",
    ):
        await hass.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )