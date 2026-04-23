async def test_other_light_update(hass: HomeAssistant, mock_bridge_v1: Mock) -> None:
    """Test changing one light that will impact state of other light."""
    mock_bridge_v1.mock_light_responses.append(LIGHT_RESPONSE)

    await setup_bridge(hass, mock_bridge_v1)
    assert len(mock_bridge_v1.mock_requests) == 2
    assert len(hass.states.async_all()) == 2

    lamp_2 = hass.states.get("light.hue_lamp_2")
    assert lamp_2 is not None
    assert lamp_2.name == "Hue Lamp 2"
    assert lamp_2.state == "off"

    updated_light_response = dict(LIGHT_RESPONSE)
    updated_light_response["2"] = {
        "state": {
            "on": True,
            "bri": 100,
            "hue": 13088,
            "sat": 210,
            "xy": [0.5, 0.4],
            "ct": 420,
            "alert": "none",
            "effect": "none",
            "colormode": "hs",
            "reachable": True,
        },
        "capabilities": LIGHT_2_CAPABILITIES,
        "type": "Extended color light",
        "name": "Hue Lamp 2 new",
        "modelid": "LCT001",
        "swversion": "66009461",
        "manufacturername": "Philips",
        "uniqueid": "123",
    }

    mock_bridge_v1.mock_light_responses.append(updated_light_response)

    # Calling a service will trigger the updates to run
    await hass.services.async_call(
        "light", "turn_on", {"entity_id": "light.hue_lamp_1"}, blocking=True
    )
    # 2x light update, 1 group update, 1 turn on request
    assert len(mock_bridge_v1.mock_requests) == 4
    assert len(hass.states.async_all()) == 2

    lamp_2 = hass.states.get("light.hue_lamp_2")
    assert lamp_2 is not None
    assert lamp_2.name == "Hue Lamp 2 New"
    assert lamp_2.state == "on"
    assert lamp_2.attributes["brightness"] == 100