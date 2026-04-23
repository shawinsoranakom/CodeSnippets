async def test_group_features(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    mock_bridge_v1: Mock,
) -> None:
    """Test group features."""
    color_temp_type = "Color temperature light"
    extended_color_type = "Extended color light"

    group_response = {
        "1": {
            "name": "Group 1",
            "lights": ["1", "2"],
            "type": "LightGroup",
            "action": {
                "on": True,
                "bri": 254,
                "hue": 10000,
                "sat": 254,
                "effect": "none",
                "xy": [0.5, 0.5],
                "ct": 250,
                "alert": "select",
                "colormode": "ct",
            },
            "state": {"any_on": True, "all_on": False},
        },
        "2": {
            "name": "Living Room",
            "lights": ["2", "3"],
            "type": "Room",
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
        },
        "3": {
            "name": "Dining Room",
            "lights": ["4"],
            "type": "Room",
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
        },
    }

    light_1 = {
        "state": {
            "on": True,
            "bri": 144,
            "ct": 467,
            "alert": "none",
            "effect": "none",
            "reachable": True,
        },
        "capabilities": {
            "control": {
                "colorgamuttype": "A",
                "colorgamut": [[0.704, 0.296], [0.2151, 0.7106], [0.138, 0.08]],
            }
        },
        "type": color_temp_type,
        "name": "Hue Lamp 1",
        "modelid": "LCT001",
        "swversion": "66009461",
        "manufacturername": "Philips",
        "uniqueid": "456",
    }
    light_2 = {
        "state": {
            "on": False,
            "bri": 0,
            "ct": 0,
            "alert": "none",
            "effect": "none",
            "colormode": "xy",
            "reachable": True,
        },
        "capabilities": {
            "control": {
                "colorgamuttype": "A",
                "colorgamut": [[0.704, 0.296], [0.2151, 0.7106], [0.138, 0.08]],
            }
        },
        "type": color_temp_type,
        "name": "Hue Lamp 2",
        "modelid": "LCT001",
        "swversion": "66009461",
        "manufacturername": "Philips",
        "uniqueid": "4567",
    }
    light_3 = {
        "state": {
            "on": False,
            "bri": 0,
            "hue": 0,
            "sat": 0,
            "xy": [0, 0],
            "ct": 0,
            "alert": "none",
            "effect": "none",
            "colormode": "hs",
            "reachable": True,
        },
        "capabilities": {
            "control": {
                "colorgamuttype": "A",
                "colorgamut": [[0.704, 0.296], [0.2151, 0.7106], [0.138, 0.08]],
            }
        },
        "type": extended_color_type,
        "name": "Hue Lamp 3",
        "modelid": "LCT001",
        "swversion": "66009461",
        "manufacturername": "Philips",
        "uniqueid": "123",
    }
    light_4 = {
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
        "capabilities": {
            "control": {
                "colorgamuttype": "A",
                "colorgamut": [[0.704, 0.296], [0.2151, 0.7106], [0.138, 0.08]],
            }
        },
        "type": extended_color_type,
        "name": "Hue Lamp 4",
        "modelid": "LCT001",
        "swversion": "66009461",
        "manufacturername": "Philips",
        "uniqueid": "1234",
    }
    light_response = {
        "1": light_1,
        "2": light_2,
        "3": light_3,
        "4": light_4,
    }

    mock_bridge_v1.mock_light_responses.append(light_response)
    mock_bridge_v1.mock_group_responses.append(group_response)
    await setup_bridge(hass, mock_bridge_v1)
    assert len(mock_bridge_v1.mock_requests) == 2

    color_temp_feature = hue_light.SUPPORT_HUE["Color temperature light"]
    color_temp_mode = sorted(hue_light.COLOR_MODES_HUE["Color temperature light"])
    extended_color_feature = hue_light.SUPPORT_HUE["Extended color light"]
    extended_color_mode = sorted(hue_light.COLOR_MODES_HUE["Extended color light"])

    group_1 = hass.states.get("light.group_1")
    assert group_1.attributes["supported_color_modes"] == color_temp_mode
    assert group_1.attributes["supported_features"] == color_temp_feature

    group_2 = hass.states.get("light.living_room")
    assert group_2.attributes["supported_color_modes"] == extended_color_mode
    assert group_2.attributes["supported_features"] == extended_color_feature

    group_3 = hass.states.get("light.dining_room")
    assert group_3.attributes["supported_color_modes"] == extended_color_mode
    assert group_3.attributes["supported_features"] == extended_color_feature

    entry = entity_registry.async_get("light.hue_lamp_1")
    device_entry = device_registry.async_get(entry.device_id)
    assert device_entry.area_id is None

    entry = entity_registry.async_get("light.hue_lamp_2")
    device_entry = device_registry.async_get(entry.device_id)
    assert (
        device_entry.area_id == area_registry.async_get_area_by_name("Living Room").id
    )

    entry = entity_registry.async_get("light.hue_lamp_3")
    device_entry = device_registry.async_get(entry.device_id)
    assert (
        device_entry.area_id == area_registry.async_get_area_by_name("Living Room").id
    )

    entry = entity_registry.async_get("light.hue_lamp_4")
    device_entry = device_registry.async_get(entry.device_id)
    assert (
        device_entry.area_id == area_registry.async_get_area_by_name("Dining Room").id
    )