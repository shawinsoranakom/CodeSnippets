async def test_fetch_constraints_after_rate_limit_error(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    retry_after: int | None,
    appliance: HomeAppliance,
    entity_id: str,
    setting_key: SettingKey,
    type: str,
    min_value: int,
    max_value: int,
    step_size: int,
    unit_of_measurement: str,
) -> None:
    """Test that, if a API rate limit error is raised, the constraints are fetched later."""

    def get_settings_side_effect(ha_id: str):
        if ha_id != appliance.ha_id:
            return ArrayOfSettings([])
        return ArrayOfSettings(
            [
                GetSetting(
                    key=setting_key,
                    raw_key=setting_key.value,
                    value=random.randint(min_value, max_value),
                )
            ]
        )

    client.get_settings = AsyncMock(side_effect=get_settings_side_effect)
    client.get_setting = AsyncMock(
        side_effect=[
            TooManyRequestsError("error.key", retry_after=retry_after),
            GetSetting(
                key=setting_key,
                raw_key=setting_key.value,
                value=random.randint(min_value, max_value),
                unit=unit_of_measurement,
                type=type,
                constraints=SettingConstraints(
                    min=min_value,
                    max=max_value,
                    step_size=step_size,
                ),
            ),
        ]
    )

    assert await integration_setup(client)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED

    assert client.get_setting.call_count == 2

    entity_state = hass.states.get(entity_id)
    assert entity_state
    attributes = entity_state.attributes
    assert attributes["min"] == min_value
    assert attributes["max"] == max_value
    assert attributes["step"] == step_size
    assert attributes["unit_of_measurement"] == unit_of_measurement