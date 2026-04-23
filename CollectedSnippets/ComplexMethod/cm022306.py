async def test_grouped_lights(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_bridge_v2: Mock,
    v2_resources_test_data: JsonArrayType,
) -> None:
    """Test if all v2 grouped lights get created with correct features."""
    await mock_bridge_v2.api.load_test_data(v2_resources_test_data)

    await setup_platform(hass, mock_bridge_v2, Platform.LIGHT)

    # test if entities for hue groups are created and enabled by default
    for entity_id in ("light.test_zone", "light.test_room"):
        entity_entry = entity_registry.async_get(entity_id)

        assert entity_entry
        # scene entities should have be assigned to the room/zone device/service
        assert entity_entry.device_id is not None

    # test light created for hue zone
    test_entity = hass.states.get("light.test_zone")
    assert test_entity is not None
    assert test_entity.attributes["friendly_name"] == "Test Zone"
    assert test_entity.state == "on"
    assert test_entity.attributes["brightness"] == 119
    assert test_entity.attributes["color_mode"] == ColorMode.XY
    assert set(test_entity.attributes["supported_color_modes"]) == {
        ColorMode.COLOR_TEMP,
        ColorMode.XY,
    }
    assert test_entity.attributes["max_color_temp_kelvin"] == 6535
    assert test_entity.attributes["min_color_temp_kelvin"] == 2000
    assert test_entity.attributes["is_hue_group"] is True
    assert test_entity.attributes["hue_scenes"] == {"Dynamic Test Scene"}
    assert test_entity.attributes["hue_type"] == "zone"
    assert test_entity.attributes["lights"] == {
        "Hue light with color and color temperature 1",
        "Hue light with color and color temperature gradient",
        "Hue light with color and color temperature 2",
    }
    assert test_entity.attributes["entity_id"] == {
        "light.hue_light_with_color_and_color_temperature_gradient",
        "light.hue_light_with_color_and_color_temperature_2",
        "light.hue_light_with_color_and_color_temperature_1",
    }

    # test light created for hue room
    test_entity = hass.states.get("light.test_room")
    assert test_entity is not None
    assert test_entity.attributes["friendly_name"] == "Test Room"
    assert test_entity.state == "off"
    assert test_entity.attributes["supported_color_modes"] == [ColorMode.COLOR_TEMP]
    assert test_entity.attributes["max_color_temp_kelvin"] == 6535
    assert test_entity.attributes["min_color_temp_kelvin"] == 2202
    assert test_entity.attributes["is_hue_group"] is True
    assert test_entity.attributes["hue_scenes"] == {
        "Regular Test Scene",
        "Smart Test Scene",
    }
    assert test_entity.attributes["hue_type"] == "room"
    assert test_entity.attributes["lights"] == {
        "Hue on/off light",
        "Hue light with color temperature only",
    }
    assert test_entity.attributes["entity_id"] == {
        "light.hue_light_with_color_temperature_only",
        "light.hue_on_off_light",
    }

    # Test calling the turn on service on a grouped light
    test_light_id = "light.test_zone"
    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": test_light_id,
            "brightness_pct": 100,
            "xy_color": (0.123, 0.123),
            "transition": 0.25,
        },
        blocking=True,
    )

    # PUT request should have been sent to group_light with correct params
    assert len(mock_bridge_v2.mock_requests) == 1
    assert mock_bridge_v2.mock_requests[0]["json"]["on"]["on"] is True
    assert mock_bridge_v2.mock_requests[0]["json"]["dimming"]["brightness"] == 100
    assert mock_bridge_v2.mock_requests[0]["json"]["color"]["xy"]["x"] == 0.123
    assert mock_bridge_v2.mock_requests[0]["json"]["color"]["xy"]["y"] == 0.123
    assert mock_bridge_v2.mock_requests[0]["json"]["dynamics"]["duration"] == 200

    # Now generate update events by emitting the json we've sent as incoming events
    for light_id in (
        "02cba059-9c2c-4d45-97e4-4f79b1bfbaa1",
        "b3fe71ef-d0ef-48de-9355-d9e604377df0",
        "8015b17f-8336-415b-966a-b364bd082397",
    ):
        event = {
            "id": light_id,
            "type": "light",
            **mock_bridge_v2.mock_requests[0]["json"],
        }
        mock_bridge_v2.api.emit_event("update", event)
    await hass.async_block_till_done()

    # The light should now be on and have the properties we've set
    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "on"
    assert test_light.attributes["color_mode"] == ColorMode.XY
    assert test_light.attributes["brightness"] == 255
    assert test_light.attributes["xy_color"] == (0.123, 0.123)

    # While we have a group on, test the color aggregation logic, XY first

    # Turn off one of the bulbs in the group
    # "hue_light_with_color_and_color_temperature_1" corresponds to "02cba059-9c2c-4d45-97e4-4f79b1bfbaa1"
    mock_bridge_v2.mock_requests.clear()
    single_light_id = "light.hue_light_with_color_and_color_temperature_1"
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": single_light_id},
        blocking=True,
    )
    event = {
        "id": "02cba059-9c2c-4d45-97e4-4f79b1bfbaa1",
        "type": "light",
        "on": {"on": False},
    }
    mock_bridge_v2.api.emit_event("update", event)
    await hass.async_block_till_done()

    # The group should still show the same XY color since other lights maintain their color
    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "on"
    assert test_light.attributes["xy_color"] == (0.123, 0.123)

    # Turn the light back on with a white XY color (different from the rest of the group)
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": single_light_id, "xy_color": [0.3127, 0.3290]},
        blocking=True,
    )
    event = {
        "id": "02cba059-9c2c-4d45-97e4-4f79b1bfbaa1",
        "type": "light",
        "on": {"on": True},
        "color": {"xy": {"x": 0.3127, "y": 0.3290}},
    }
    mock_bridge_v2.api.emit_event("update", event)
    await hass.async_block_till_done()

    # Now the group XY color should be the average of all three lights:
    # Light 1: (0.3127, 0.3290) - white
    # Light 2: (0.123, 0.123)
    # Light 3: (0.123, 0.123)
    # Average: ((0.3127 + 0.123 + 0.123) / 3, (0.3290 + 0.123 + 0.123) / 3)
    # Average: (0.1862, 0.1917) rounded to 4 decimal places
    expected_x = round((0.3127 + 0.123 + 0.123) / 3, 4)
    expected_y = round((0.3290 + 0.123 + 0.123) / 3, 4)

    # Check that the group XY color is now the average of all lights
    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "on"
    group_x, group_y = test_light.attributes["xy_color"]
    assert abs(group_x - expected_x) < 0.001  # Allow small floating point differences
    assert abs(group_y - expected_y) < 0.001

    # Test turning off another light in the group, leaving only two lights on - one white and one original color
    # "hue_light_with_color_and_color_temperature_2" corresponds to "b3fe71ef-d0ef-48de-9355-d9e604377df0"
    second_light_id = "light.hue_light_with_color_and_color_temperature_2"
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": second_light_id},
        blocking=True,
    )

    # Simulate the second light turning off
    event = {
        "id": "b3fe71ef-d0ef-48de-9355-d9e604377df0",
        "type": "light",
        "on": {"on": False},
    }
    mock_bridge_v2.api.emit_event("update", event)
    await hass.async_block_till_done()

    # Now only two lights are on:
    # Light 1: (0.3127, 0.3290) - white
    # Light 3: (0.123, 0.123) - original color
    # Average of remaining lights: ((0.3127 + 0.123) / 2, (0.3290 + 0.123) / 2)
    expected_x_two_lights = round((0.3127 + 0.123) / 2, 4)
    expected_y_two_lights = round((0.3290 + 0.123) / 2, 4)

    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "on"
    # Check that the group color is now the average of only the two remaining lights
    group_x, group_y = test_light.attributes["xy_color"]
    assert abs(group_x - expected_x_two_lights) < 0.001
    assert abs(group_y - expected_y_two_lights) < 0.001

    # Test colour temperature aggregation
    # Set all three lights to colour temperature mode with different mirek values
    for mirek, light_name, light_id in zip(
        [300, 250, 200],
        [
            "light.hue_light_with_color_and_color_temperature_1",
            "light.hue_light_with_color_and_color_temperature_2",
            "light.hue_light_with_color_and_color_temperature_gradient",
        ],
        [
            "02cba059-9c2c-4d45-97e4-4f79b1bfbaa1",
            "b3fe71ef-d0ef-48de-9355-d9e604377df0",
            "8015b17f-8336-415b-966a-b364bd082397",
        ],
        strict=True,
    ):
        await hass.services.async_call(
            "light",
            "turn_on",
            {
                "entity_id": light_name,
                "color_temp_kelvin": color_util.color_temperature_mired_to_kelvin(
                    mirek
                ),
            },
            blocking=True,
        )
        # Emit update event with matching mirek value
        mock_bridge_v2.api.emit_event(
            "update",
            {
                "id": light_id,
                "type": "light",
                "on": {"on": True},
                "color_temperature": {"mirek": mirek, "mirek_valid": True},
            },
        )
    await hass.async_block_till_done()

    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "on"
    assert test_light.attributes["color_mode"] == ColorMode.COLOR_TEMP

    # Expected average kelvin calculation:
    # 300 mirek ≈ 3333K, 250 mirek ≈ 4000K, 200 mirek ≈ 5000K
    expected_avg_kelvin = round((3333 + 4000 + 5000) / 3)
    assert abs(test_light.attributes["color_temp_kelvin"] - expected_avg_kelvin) <= 5

    # Switch light 3 off and check average kelvin temperature of remaining two lights
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": "light.hue_light_with_color_and_color_temperature_gradient"},
        blocking=True,
    )
    event = {
        "id": "8015b17f-8336-415b-966a-b364bd082397",
        "type": "light",
        "on": {"on": False},
    }
    mock_bridge_v2.api.emit_event("update", event)
    await hass.async_block_till_done()

    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "on"
    assert test_light.attributes["color_mode"] == ColorMode.COLOR_TEMP

    # Expected average kelvin calculation:
    # 300 mirek ≈ 3333K, 250 mirek ≈ 4000K
    expected_avg_kelvin = round((3333 + 4000) / 2)
    assert abs(test_light.attributes["color_temp_kelvin"] - expected_avg_kelvin) <= 5

    # Turn light 3 back on in XY mode and verify majority still favours COLOR_TEMP
    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": "light.hue_light_with_color_and_color_temperature_gradient",
            "xy_color": [0.123, 0.123],
        },
        blocking=True,
    )
    mock_bridge_v2.api.emit_event(
        "update",
        {
            "id": "8015b17f-8336-415b-966a-b364bd082397",
            "type": "light",
            "on": {"on": True},
            "color": {"xy": {"x": 0.123, "y": 0.123}},
            "color_temperature": {
                "mirek": None,
                "mirek_valid": False,
            },
        },
    )
    await hass.async_block_till_done()

    test_light = hass.states.get(test_light_id)
    assert test_light.attributes["color_mode"] == ColorMode.COLOR_TEMP

    # Switch light 2 to XY mode to flip the majority
    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": "light.hue_light_with_color_and_color_temperature_2",
            "xy_color": [0.321, 0.321],
        },
        blocking=True,
    )
    mock_bridge_v2.api.emit_event(
        "update",
        {
            "id": "b3fe71ef-d0ef-48de-9355-d9e604377df0",
            "type": "light",
            "on": {"on": True},
            "color": {"xy": {"x": 0.321, "y": 0.321}},
            "color_temperature": {
                "mirek": None,
                "mirek_valid": False,
            },
        },
    )
    await hass.async_block_till_done()

    test_light = hass.states.get(test_light_id)
    assert test_light.attributes["color_mode"] == ColorMode.XY

    # Test brightness aggregation with different brightness levels
    mock_bridge_v2.mock_requests.clear()

    # Set all three lights to different brightness levels
    for brightness, light_name, light_id in zip(
        [90.0, 60.0, 30.0],
        [
            "light.hue_light_with_color_and_color_temperature_1",
            "light.hue_light_with_color_and_color_temperature_2",
            "light.hue_light_with_color_and_color_temperature_gradient",
        ],
        [
            "02cba059-9c2c-4d45-97e4-4f79b1bfbaa1",
            "b3fe71ef-d0ef-48de-9355-d9e604377df0",
            "8015b17f-8336-415b-966a-b364bd082397",
        ],
        strict=True,
    ):
        await hass.services.async_call(
            "light",
            "turn_on",
            {
                "entity_id": light_name,
                "brightness": brightness,
            },
            blocking=True,
        )
        # Emit update event with matching brightness value
        mock_bridge_v2.api.emit_event(
            "update",
            {
                "id": light_id,
                "type": "light",
                "on": {"on": True},
                "dimming": {"brightness": brightness},
            },
        )
    await hass.async_block_till_done()

    # Check that the group brightness is the average of all three lights
    # Expected average: (90 + 60 + 30) / 3 = 60% -> 153 (60% of 255)
    expected_brightness = round(((90 + 60 + 30) / 3 / 100) * 255)

    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "on"
    assert test_light.attributes["brightness"] == expected_brightness

    # Turn off the dimmest light 3 (30% brightness) while keeping the other two on
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": "light.hue_light_with_color_and_color_temperature_gradient"},
        blocking=True,
    )
    event = {
        "id": "8015b17f-8336-415b-966a-b364bd082397",
        "type": "light",
        "on": {"on": False},
    }
    mock_bridge_v2.api.emit_event("update", event)
    await hass.async_block_till_done()

    # Check that the group brightness is now the average of the two remaining lights
    # Expected average: (90 + 60) / 2 = 75% -> 191 (75% of 255)
    expected_brightness_two_lights = round(((90 + 60) / 2 / 100) * 255)

    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "on"
    assert test_light.attributes["brightness"] == expected_brightness_two_lights

    # Turn off light 2 (60% brightness), leaving only the brightest one
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": "light.hue_light_with_color_and_color_temperature_2"},
        blocking=True,
    )
    event = {
        "id": "b3fe71ef-d0ef-48de-9355-d9e604377df0",
        "type": "light",
        "on": {"on": False},
    }
    mock_bridge_v2.api.emit_event("update", event)
    await hass.async_block_till_done()

    # Check that the group brightness is now just the remaining light's brightness
    # Expected brightness: 90% -> 230 (round(90 / 100 * 255))
    expected_brightness_one_light = round((90 / 100) * 255)

    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "on"
    assert test_light.attributes["brightness"] == expected_brightness_one_light

    # Set all three lights back to 100% brightness for consistency with later tests
    for light_name, light_id in zip(
        [
            "light.hue_light_with_color_and_color_temperature_1",
            "light.hue_light_with_color_and_color_temperature_2",
            "light.hue_light_with_color_and_color_temperature_gradient",
        ],
        [
            "02cba059-9c2c-4d45-97e4-4f79b1bfbaa1",
            "b3fe71ef-d0ef-48de-9355-d9e604377df0",
            "8015b17f-8336-415b-966a-b364bd082397",
        ],
        strict=True,
    ):
        await hass.services.async_call(
            "light",
            "turn_on",
            {
                "entity_id": light_name,
                "brightness": 100.0,
            },
            blocking=True,
        )
        # Emit update event with matching brightness value
        mock_bridge_v2.api.emit_event(
            "update",
            {
                "id": light_id,
                "type": "light",
                "on": {"on": True},
                "dimming": {"brightness": 100.0},
            },
        )
    await hass.async_block_till_done()

    # Verify group is back to 100% brightness
    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "on"
    assert test_light.attributes["brightness"] == 255

    # Test calling the turn off service on a grouped light.
    mock_bridge_v2.mock_requests.clear()
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": test_light_id},
        blocking=True,
    )

    # PUT request should have been sent to ONLY the grouped_light resource with correct params
    assert len(mock_bridge_v2.mock_requests) == 1
    assert mock_bridge_v2.mock_requests[0]["method"] == "put"
    assert mock_bridge_v2.mock_requests[0]["json"]["on"]["on"] is False

    # Now generate update event by emitting the json we've sent as incoming event
    event = {
        "id": "f2416154-9607-43ab-a684-4453108a200e",
        "type": "grouped_light",
        **mock_bridge_v2.mock_requests[0]["json"],
    }
    mock_bridge_v2.api.emit_event("update", event)
    mock_bridge_v2.api.emit_event("update", mock_bridge_v2.mock_requests[0]["json"])
    await hass.async_block_till_done()

    # the light should now be off
    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "off"

    # Test calling the turn off service on a grouped light with transition
    mock_bridge_v2.mock_requests.clear()
    test_light_id = "light.test_zone"
    await hass.services.async_call(
        "light",
        "turn_off",
        {
            "entity_id": test_light_id,
            "transition": 0.25,
        },
        blocking=True,
    )

    # PUT request should have been sent to group_light with correct params
    assert len(mock_bridge_v2.mock_requests) == 1
    assert mock_bridge_v2.mock_requests[0]["json"]["on"]["on"] is False
    assert mock_bridge_v2.mock_requests[0]["json"]["dynamics"]["duration"] == 200

    # Test turn_on resets brightness
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 2
    assert mock_bridge_v2.mock_requests[1]["json"]["on"]["on"] is True
    assert mock_bridge_v2.mock_requests[1]["json"]["dimming"]["brightness"] == 100

    # Test sending short flash effect to a grouped light
    mock_bridge_v2.mock_requests.clear()
    test_light_id = "light.test_zone"
    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": test_light_id,
            "flash": "short",
        },
        blocking=True,
    )

    # PUT request should have been sent to ALL group lights with correct params
    assert len(mock_bridge_v2.mock_requests) == 3
    for index in range(3):
        assert (
            mock_bridge_v2.mock_requests[index]["json"]["identify"]["action"]
            == "identify"
        )

    # Test sending long flash effect to a grouped light
    mock_bridge_v2.mock_requests.clear()
    test_light_id = "light.test_zone"
    await hass.services.async_call(
        "light",
        "turn_on",
        {
            "entity_id": test_light_id,
            "flash": "long",
        },
        blocking=True,
    )

    # PUT request should have been sent to grouped_light with correct params
    assert len(mock_bridge_v2.mock_requests) == 1
    assert mock_bridge_v2.mock_requests[0]["json"]["alert"]["action"] == "breathe"

    # Test sending flash effect in turn_off call
    mock_bridge_v2.mock_requests.clear()
    test_light_id = "light.test_zone"
    await hass.services.async_call(
        "light",
        "turn_off",
        {
            "entity_id": test_light_id,
            "flash": "short",
        },
        blocking=True,
    )

    # PUT request should have been sent to ALL group lights with correct params
    assert len(mock_bridge_v2.mock_requests) == 3
    for index in range(3):
        assert (
            mock_bridge_v2.mock_requests[index]["json"]["identify"]["action"]
            == "identify"
        )