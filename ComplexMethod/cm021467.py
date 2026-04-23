async def test_flux_before_sunrise(
    hass: HomeAssistant,
    mock_light_entities: list[MockLight],
) -> None:
    """Test the flux switch before sunrise."""
    setup_test_component_platform(hass, light.DOMAIN, mock_light_entities)

    assert await async_setup_component(
        hass, light.DOMAIN, {light.DOMAIN: {CONF_PLATFORM: "test"}}
    )
    await hass.async_block_till_done()

    ent1 = mock_light_entities[0]

    # Verify initial state of light
    state = hass.states.get(ent1.entity_id)
    assert state.state == STATE_ON
    assert state.attributes.get("xy_color") is None
    assert state.attributes.get("brightness") is None

    test_time = dt_util.utcnow().replace(hour=2, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=5)

    def event_date(
        hass: HomeAssistant, event: str, now: date | datetime | None = None
    ) -> datetime | None:
        if event == SUN_EVENT_SUNRISE:
            return sunrise_time
        return sunset_time

    await hass.async_block_till_done()
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
                    "lights": [ent1.entity_id],
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
    assert call.data[light.ATTR_BRIGHTNESS] == 112
    assert call.data[light.ATTR_XY_COLOR] == [0.606, 0.379]