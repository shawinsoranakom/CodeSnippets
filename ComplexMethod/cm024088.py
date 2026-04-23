async def test_cloud_heater(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    functional_cloud_heater: MagicMock,
    cloud_heater_control: MagicMock,
    cloud_heater_set_temp: MagicMock,
    before_state: HVACMode,
    before_attrs: dict,
    service_name: str,
    service_params: dict,
    effect: contextlib.AbstractContextManager,
    heater_control_calls: list,
    heater_set_temp_calls: list,
    after_state: HVACMode,
    after_attrs: dict,
) -> None:
    """Tests setting HVAC mode (directly or through set_temperature) for a cloud heater."""

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

    cloud_heater_control.assert_has_calls(heater_control_calls)
    cloud_heater_set_temp.assert_has_calls(heater_set_temp_calls)

    state = hass.states.get(ENTITY_CLIMATE)
    assert state is not None
    assert state.state == after_state
    for attr, value in after_attrs.items():
        assert state.attributes.get(attr) == value