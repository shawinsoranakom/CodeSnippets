async def test_new_group_discovered(hass: HomeAssistant, mock_bridge_v1: Mock) -> None:
    """Test if 2nd update has a new group."""
    mock_bridge_v1.allow_groups = True
    mock_bridge_v1.mock_light_responses.append({})
    mock_bridge_v1.mock_group_responses.append(GROUP_RESPONSE)

    await setup_bridge(hass, mock_bridge_v1)
    assert len(mock_bridge_v1.mock_requests) == 2
    assert len(hass.states.async_all()) == 2

    new_group_response = dict(GROUP_RESPONSE)
    new_group_response["3"] = {
        "name": "Group 3",
        "lights": ["3", "4", "5"],
        "type": "LightGroup",
        "action": {
            "on": True,
            "bri": 153,
            "hue": 4345,
            "sat": 254,
            "effect": "none",
            "xy": [0.5, 0.5],
            "ct": 250,
            "alert": "select",
            "colormode": "ct",
        },
        "state": {"any_on": True, "all_on": False},
    }

    mock_bridge_v1.mock_light_responses.append({})
    mock_bridge_v1.mock_group_responses.append(new_group_response)

    # Calling a service will trigger the updates to run
    await hass.services.async_call(
        "light", "turn_on", {"entity_id": "light.group_1"}, blocking=True
    )
    # 2x group update, 1x light update, 1 turn on request
    assert len(mock_bridge_v1.mock_requests) == 4
    assert len(hass.states.async_all()) == 3

    new_group = hass.states.get("light.group_3")
    assert new_group is not None
    assert new_group.state == "on"
    assert new_group.attributes["brightness"] == 154
    assert new_group.attributes["color_temp_kelvin"] == 4000