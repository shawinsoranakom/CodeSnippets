async def test_local_heater(
    hass: HomeAssistant,
    functional_local_heater: MagicMock,
    local_heater_set_mode_control_individually: MagicMock,
    local_heater_set_mode_off: MagicMock,
    local_heater_set_target_temperature: MagicMock,
    before_state: HVACMode,
    before_attrs: dict,
    service_name: str,
    service_params: dict,
    effect: contextlib.AbstractContextManager,
    heater_mode_set_individually_calls: list,
    heater_mode_set_off_calls: list,
    heater_set_target_temperature_calls: list,
    after_state: HVACMode,
    after_attrs: dict,
) -> None:
    """Tests setting HVAC mode (directly or through set_temperature) for a local heater."""

    state = hass.states.get(ENTITY_CLIMATE)
    assert state is not None
    assert state.state == before_state
    for attr, value in before_attrs.items():
        assert state.attributes.get(attr) == value

    with effect:
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            service_name,
            service_params | {ATTR_ENTITY_ID: ENTITY_CLIMATE},
            blocking=True,
        )
    await hass.async_block_till_done()

    local_heater_set_mode_control_individually.assert_has_calls(
        heater_mode_set_individually_calls
    )
    local_heater_set_mode_off.assert_has_calls(heater_mode_set_off_calls)
    local_heater_set_target_temperature.assert_has_calls(
        heater_set_target_temperature_calls
    )

    state = hass.states.get(ENTITY_CLIMATE)
    assert state is not None
    assert state.state == after_state
    for attr, value in after_attrs.items():
        assert state.attributes.get(attr) == value