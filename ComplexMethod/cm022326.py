async def test_light_turn_off_service(
    hass: HomeAssistant, mock_bridge_v1: Mock
) -> None:
    """Test calling the turn on service on a light."""
    mock_bridge_v1.mock_light_responses.append(LIGHT_RESPONSE)

    await setup_bridge(hass, mock_bridge_v1)
    light = hass.states.get("light.hue_lamp_1")
    assert light is not None
    assert light.state == "on"

    updated_light_response = dict(LIGHT_RESPONSE)
    updated_light_response["1"] = LIGHT_1_OFF

    mock_bridge_v1.mock_light_responses.append(updated_light_response)

    await hass.services.async_call(
        "light", "turn_off", {"entity_id": "light.hue_lamp_1"}, blocking=True
    )

    # 2x light update, 1 for group update, 1 turn on request
    assert len(mock_bridge_v1.mock_requests) == 4

    assert mock_bridge_v1.mock_requests[2]["json"] == {"on": False, "alert": "none"}

    assert len(hass.states.async_all()) == 2

    light = hass.states.get("light.hue_lamp_1")
    assert light is not None
    assert light.state == "off"