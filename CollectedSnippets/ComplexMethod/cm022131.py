async def test_icon_and_state(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test to ensure state and custom icons are returned."""
    await asyncio.gather(
        *[
            async_setup_component(hass, comp, {})
            for comp in ("homeassistant", "logbook")
        ]
    )

    await async_recorder_block_till_done(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)

    hass.states.async_set("light.kitchen", STATE_OFF, {"icon": "mdi:chemical-weapon"})
    hass.states.async_set(
        "light.kitchen", STATE_ON, {"brightness": 100, "icon": "mdi:security"}
    )
    hass.states.async_set(
        "light.kitchen", STATE_ON, {"brightness": 200, "icon": "mdi:security"}
    )
    hass.states.async_set(
        "light.kitchen", STATE_ON, {"brightness": 300, "icon": "mdi:security"}
    )
    hass.states.async_set(
        "light.kitchen", STATE_ON, {"brightness": 400, "icon": "mdi:security"}
    )
    hass.states.async_set("light.kitchen", STATE_OFF, {"icon": "mdi:chemical-weapon"})

    await async_wait_recording_done(hass)

    client = await hass_client()
    response_json = await _async_fetch_logbook(client)

    assert len(response_json) == 3
    assert response_json[0]["domain"] == "homeassistant"
    assert response_json[1]["entity_id"] == "light.kitchen"
    assert response_json[1]["icon"] == "mdi:security"
    assert response_json[1]["state"] == STATE_ON
    assert response_json[2]["entity_id"] == "light.kitchen"
    assert response_json[2]["icon"] == "mdi:chemical-weapon"
    assert response_json[2]["state"] == STATE_OFF