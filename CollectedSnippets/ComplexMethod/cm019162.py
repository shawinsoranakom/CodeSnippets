async def test_number_entity_functionality(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
    entity_id: str,
    setting_key: SettingKey,
    type: str,
    expected_state: int,
    min_value: int,
    max_value: int,
    step_size: float,
    unit_of_measurement: str,
) -> None:
    """Test number entity functionality."""
    client.get_setting.side_effect = None
    client.get_setting = AsyncMock(
        return_value=GetSetting(
            key=setting_key,
            raw_key=setting_key.value,
            value="",  # This should not change the value
            unit=unit_of_measurement,
            type=type,
            constraints=SettingConstraints(
                min=min_value,
                max=max_value,
                step_size=step_size if isinstance(step_size, int) else None,
            ),
        )
    )

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED
    entity_state = hass.states.get(entity_id)
    assert entity_state
    assert entity_state.state == str(expected_state)
    attributes = entity_state.attributes
    assert attributes["min"] == min_value
    assert attributes["max"] == max_value
    assert attributes["step"] == step_size
    assert attributes["unit_of_measurement"] == unit_of_measurement

    value = random.choice(
        [num for num in range(min_value, max_value + 1) if num != expected_state]
    )
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: entity_id,
            SERVICE_ATTR_VALUE: value,
        },
    )
    await hass.async_block_till_done()
    client.set_setting.assert_awaited_once_with(
        appliance.ha_id, setting_key=setting_key, value=value
    )
    assert hass.states.is_state(entity_id, str(float(value)))