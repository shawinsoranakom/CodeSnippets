async def test_light_turn_on_service(hass: HomeAssistant, mock_bridge_v1: Mock) -> None:
    """Test calling the turn on service on a light."""
    mock_bridge_v1.mock_light_responses.append(LIGHT_RESPONSE)

    await setup_bridge(hass, mock_bridge_v1)
    light = hass.states.get("light.hue_lamp_2")
    assert light is not None
    assert light.state == "off"

    updated_light_response = dict(LIGHT_RESPONSE)
    updated_light_response["2"] = LIGHT_2_ON

    mock_bridge_v1.mock_light_responses.append(updated_light_response)

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.hue_lamp_2", "brightness": 100, "color_temp_kelvin": 3333},
        blocking=True,
    )
    # 2x light update, 1x group update, 1 turn on request
    assert len(mock_bridge_v1.mock_requests) == 4

    assert mock_bridge_v1.mock_requests[2]["json"] == {
        "bri": 100,
        "on": True,
        "ct": 300,
        "alert": "none",
    }

    assert len(hass.states.async_all()) == 2

    light = hass.states.get("light.hue_lamp_2")
    assert light is not None
    assert light.state == "on"

    # test hue gamut in turn_on service
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.hue_lamp_2", "rgb_color": [0, 0, 255]},
        blocking=True,
    )

    assert len(mock_bridge_v1.mock_requests) == 5

    assert mock_bridge_v1.mock_requests[4]["json"] == {
        "on": True,
        "xy": (0.138, 0.08),
        "alert": "none",
    }