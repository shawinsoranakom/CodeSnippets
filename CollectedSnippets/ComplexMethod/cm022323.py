async def test_other_group_update(hass: HomeAssistant, mock_bridge_v1: Mock) -> None:
    """Test changing one group that will impact the state of other light."""
    mock_bridge_v1.allow_groups = True
    mock_bridge_v1.mock_light_responses.append({})
    mock_bridge_v1.mock_group_responses.append(GROUP_RESPONSE)

    await setup_bridge(hass, mock_bridge_v1)
    assert len(mock_bridge_v1.mock_requests) == 2
    assert len(hass.states.async_all()) == 2

    group_2 = hass.states.get("light.group_2")
    assert group_2 is not None
    assert group_2.name == "Group 2"
    assert group_2.state == "on"
    assert group_2.attributes["brightness"] == 154
    assert group_2.attributes["color_temp_kelvin"] == 4000

    updated_group_response = dict(GROUP_RESPONSE)
    updated_group_response["2"] = {
        "name": "Group 2 new",
        "lights": ["3", "4", "5"],
        "type": "LightGroup",
        "action": {
            "on": False,
            "bri": 0,
            "hue": 0,
            "sat": 0,
            "effect": "none",
            "xy": [0, 0],
            "ct": 0,
            "alert": "none",
            "colormode": "ct",
        },
        "state": {"any_on": False, "all_on": False},
    }

    mock_bridge_v1.mock_light_responses.append({})
    mock_bridge_v1.mock_group_responses.append(updated_group_response)

    # Calling a service will trigger the updates to run
    await hass.services.async_call(
        "light", "turn_on", {"entity_id": "light.group_1"}, blocking=True
    )
    # 2x group update, 1x light update, 1 turn on request
    assert len(mock_bridge_v1.mock_requests) == 4
    assert len(hass.states.async_all()) == 2

    group_2 = hass.states.get("light.group_2")
    assert group_2 is not None
    assert group_2.name == "Group 2 new"
    assert group_2.state == "off"