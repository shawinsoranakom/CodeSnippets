async def test_lights_color_mode(hass: HomeAssistant, mock_bridge_v1: Mock) -> None:
    """Test that lights only report appropriate color mode."""
    mock_bridge_v1.mock_light_responses.append(LIGHT_RESPONSE)
    mock_bridge_v1.mock_group_responses.append(GROUP_RESPONSE)

    await setup_bridge(hass, mock_bridge_v1)

    lamp_1 = hass.states.get("light.hue_lamp_1")
    assert lamp_1 is not None
    assert lamp_1.state == "on"
    assert lamp_1.attributes["brightness"] == 145
    assert lamp_1.attributes["hs_color"] == (36.067, 69.804)
    assert lamp_1.attributes["color_temp_kelvin"] is None
    assert lamp_1.attributes["color_mode"] == ColorMode.HS
    assert lamp_1.attributes["supported_color_modes"] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
    ]

    new_light1_on = LIGHT_1_ON.copy()
    new_light1_on["state"] = new_light1_on["state"].copy()
    new_light1_on["state"]["colormode"] = "ct"
    mock_bridge_v1.mock_light_responses.append({"1": new_light1_on})
    mock_bridge_v1.mock_group_responses.append({})

    # Calling a service will trigger the updates to run
    await hass.services.async_call(
        "light", "turn_on", {"entity_id": "light.hue_lamp_2"}, blocking=True
    )
    # 2x light update, 1 group update, 1 turn on request
    assert len(mock_bridge_v1.mock_requests) == 4

    lamp_1 = hass.states.get("light.hue_lamp_1")
    assert lamp_1 is not None
    assert lamp_1.state == "on"
    assert lamp_1.attributes["brightness"] == 145
    assert lamp_1.attributes["color_temp_kelvin"] == 2141
    assert "hs_color" in lamp_1.attributes
    assert lamp_1.attributes["color_mode"] == ColorMode.COLOR_TEMP
    assert lamp_1.attributes["supported_color_modes"] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
    ]