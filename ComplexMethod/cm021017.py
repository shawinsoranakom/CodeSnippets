async def test_activate_scene(hass: HomeAssistant, entities: list[MockLight]) -> None:
    """Test active scene."""
    light_1, light_2 = await setup_lights(hass, entities)

    assert await async_setup_component(
        hass,
        scene.DOMAIN,
        {
            "scene": [
                {
                    "name": "test",
                    "entities": {
                        light_1.entity_id: "on",
                        light_2.entity_id: {"state": "on", "brightness": 100},
                    },
                }
            ]
        },
    )
    await hass.async_block_till_done()

    assert hass.states.get("scene.test").state == STATE_UNKNOWN

    now = dt_util.utcnow()
    with patch("homeassistant.core.dt_util.utcnow", return_value=now):
        await activate(hass, "scene.test")

    assert hass.states.get("scene.test").state == now.isoformat()

    assert light.is_on(hass, light_1.entity_id)
    assert light.is_on(hass, light_2.entity_id)
    assert light_2.last_call("turn_on")[1].get("brightness") == 100

    await turn_off_lights(hass, [light_2.entity_id])

    calls = async_mock_service(hass, "light", "turn_on")

    now = dt_util.utcnow()
    with patch("homeassistant.core.dt_util.utcnow", return_value=now):
        await hass.services.async_call(
            scene.DOMAIN, "turn_on", {"transition": 42, "entity_id": "scene.test"}
        )
        await hass.async_block_till_done()

    assert hass.states.get("scene.test").state == now.isoformat()

    assert len(calls) == 1
    assert calls[0].domain == "light"
    assert calls[0].service == "turn_on"
    assert calls[0].data.get("transition") == 42