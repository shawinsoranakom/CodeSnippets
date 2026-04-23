async def test_apply_service(hass: HomeAssistant) -> None:
    """Test the apply service."""
    assert await async_setup_component(hass, "scene", {})
    assert await async_setup_component(hass, "light", {"light": {"platform": "demo"}})
    await hass.async_block_till_done()

    await hass.services.async_call(
        "scene", "apply", {"entities": {"light.bed_light": "off"}}, blocking=True
    )

    assert hass.states.get("light.bed_light").state == "off"

    await hass.services.async_call(
        "scene",
        "apply",
        {"entities": {"light.bed_light": {"state": "on", "brightness": 50}}},
        blocking=True,
    )

    state = hass.states.get("light.bed_light")
    assert state.state == "on"
    assert state.attributes["brightness"] == 50

    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    await hass.services.async_call(
        "scene",
        "apply",
        {
            "transition": 42,
            "entities": {"light.bed_light": {"state": "on", "brightness": 50}},
        },
        blocking=True,
    )

    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].domain == "light"
    assert turn_on_calls[0].service == "turn_on"
    assert turn_on_calls[0].data.get("transition") == 42
    assert turn_on_calls[0].data.get("entity_id") == "light.bed_light"
    assert turn_on_calls[0].data.get("brightness") == 50