async def test_lights(hass: HomeAssistant, mock_bridge_v1: Mock) -> None:
    """Test the update_lights function with some lights."""
    mock_bridge_v1.mock_light_responses.append(LIGHT_RESPONSE)

    await setup_bridge(hass, mock_bridge_v1)
    assert len(mock_bridge_v1.mock_requests) == 2
    # 2 lights
    assert len(hass.states.async_all()) == 2

    lamp_1 = hass.states.get("light.hue_lamp_1")
    assert lamp_1 is not None
    assert lamp_1.state == "on"
    assert lamp_1.attributes["brightness"] == 145
    assert lamp_1.attributes["hs_color"] == (36.067, 69.804)

    lamp_2 = hass.states.get("light.hue_lamp_2")
    assert lamp_2 is not None
    assert lamp_2.state == "off"