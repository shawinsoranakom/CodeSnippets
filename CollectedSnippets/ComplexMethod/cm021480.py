async def test_flux_with_multiple_lights(
    hass: HomeAssistant,
    mock_light_entities: list[MockLight],
) -> None:
    """Test the flux switch with multiple light entities."""
    setup_test_component_platform(hass, light.DOMAIN, mock_light_entities)

    assert await async_setup_component(
        hass, light.DOMAIN, {light.DOMAIN: {CONF_PLATFORM: "test"}}
    )
    await hass.async_block_till_done()

    ent1, ent2, ent3 = mock_light_entities

    await hass.services.async_call(
        light.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ent2.entity_id}, blocking=True
    )
    await hass.services.async_call(
        light.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ent3.entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    state = hass.states.get(ent1.entity_id)
    assert state.state == STATE_ON
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get("brightness") is None

    state = hass.states.get(ent2.entity_id)
    assert state.state == STATE_ON
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get("brightness") is None

    state = hass.states.get(ent3.entity_id)
    assert state.state == STATE_ON
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get("brightness") is None

    test_time = dt_util.utcnow().replace(hour=12, minute=0, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)

    def event_date(
        hass: HomeAssistant, event: str, now: date | datetime | None = None
    ) -> datetime | None:
        if event == SUN_EVENT_SUNRISE:
            return sunrise_time
        return sunset_time

    with (
        freeze_time(test_time),
        patch(
            "homeassistant.components.flux.switch.get_astral_event_date",
            side_effect=event_date,
        ),
    ):
        assert await async_setup_component(
            hass,
            switch.DOMAIN,
            {
                switch.DOMAIN: {
                    "platform": "flux",
                    "name": "flux",
                    "lights": [ent1.entity_id, ent2.entity_id, ent3.entity_id],
                }
            },
        )
        await hass.async_block_till_done()
        turn_on_calls = async_mock_service(hass, light.DOMAIN, SERVICE_TURN_ON)
        await hass.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.flux"},
            blocking=True,
        )
        async_fire_time_changed(hass, test_time)
        await hass.async_block_till_done()
    call = turn_on_calls[-1]
    assert call.data[light.ATTR_BRIGHTNESS] == 163
    assert call.data[light.ATTR_XY_COLOR] == [0.46, 0.376]
    call = turn_on_calls[-2]
    assert call.data[light.ATTR_BRIGHTNESS] == 163
    assert call.data[light.ATTR_XY_COLOR] == [0.46, 0.376]
    call = turn_on_calls[-3]
    assert call.data[light.ATTR_BRIGHTNESS] == 163
    assert call.data[light.ATTR_XY_COLOR] == [0.46, 0.376]