async def test_light_turn_on_service(
    hass: HomeAssistant, mock_bridge_v2: Mock, v2_resources_test_data: JsonArrayType
) -> None:
    """Test calling the turn on service on a light."""
    await mock_bridge_v2.api.load_test_data(v2_resources_test_data)

    await setup_platform(hass, mock_bridge_v2, Platform.LIGHT)

    test_light_id = "light.hue_light_with_color_temperature_only"

    # verify the light is off before we start
    assert hass.states.get(test_light_id).state == "off"

    # now call the HA turn_on service
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id, "brightness_pct": 100, "color_temp_kelvin": 3333},
        blocking=True,
    )

    # PUT request should have been sent to device with correct params
    assert len(mock_bridge_v2.mock_requests) == 1
    assert mock_bridge_v2.mock_requests[0]["method"] == "put"
    assert mock_bridge_v2.mock_requests[0]["json"]["on"]["on"] is True
    assert mock_bridge_v2.mock_requests[0]["json"]["dimming"]["brightness"] == 100
    assert mock_bridge_v2.mock_requests[0]["json"]["color_temperature"]["mirek"] == 300

    # Now generate update event by emitting the json we've sent as incoming event
    event = {
        "id": "3a6710fa-4474-4eba-b533-5e6e72968feb",
        "type": "light",
        **mock_bridge_v2.mock_requests[0]["json"],
    }
    mock_bridge_v2.api.emit_event("update", event)
    await hass.async_block_till_done()

    # the light should now be on
    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "on"
    assert test_light.attributes["mode"] == "normal"
    assert test_light.attributes["supported_color_modes"] == [ColorMode.COLOR_TEMP]
    assert test_light.attributes["color_mode"] == ColorMode.COLOR_TEMP
    assert test_light.attributes["brightness"] == 255

    # test again with sending transition with 250ms which should round up to 200ms
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id, "brightness_pct": 50, "transition": 0.25},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 2
    assert mock_bridge_v2.mock_requests[1]["json"]["on"]["on"] is True
    assert mock_bridge_v2.mock_requests[1]["json"]["dynamics"]["duration"] == 200

    # test again with sending long flash
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id, "flash": "long"},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 3
    assert mock_bridge_v2.mock_requests[2]["json"]["alert"]["action"] == "breathe"

    # test again with sending short flash
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id, "flash": "short"},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 4
    assert mock_bridge_v2.mock_requests[3]["json"]["identify"]["action"] == "identify"

    # test again with sending a colortemperature which is out of range
    # which should be normalized to the upper/lower bounds Hue can handle
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id, "color_temp_kelvin": 20000},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 5
    assert mock_bridge_v2.mock_requests[4]["json"]["color_temperature"]["mirek"] == 153
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id, "color_temp_kelvin": 1818},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 6
    assert mock_bridge_v2.mock_requests[5]["json"]["color_temperature"]["mirek"] == 454

    # test enable an effect
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id, "effect": "candle"},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 7
    assert mock_bridge_v2.mock_requests[6]["json"]["effects"]["effect"] == "candle"
    # fire event to update effect in HA state
    event = {
        "id": "3a6710fa-4474-4eba-b533-5e6e72968feb",
        "type": "light",
        "effects": {"status": "candle"},
    }
    mock_bridge_v2.api.emit_event("update", event)
    await hass.async_block_till_done()
    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.attributes["effect"] == "candle"

    # test disable effect
    # it should send a request with effect set to "no_effect"
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id, "effect": "off"},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 8
    assert mock_bridge_v2.mock_requests[7]["json"]["effects"]["effect"] == "no_effect"
    # fire event to update effect in HA state
    event = {
        "id": "3a6710fa-4474-4eba-b533-5e6e72968feb",
        "type": "light",
        "effects": {"status": "no_effect"},
    }
    mock_bridge_v2.api.emit_event("update", event)
    await hass.async_block_till_done()
    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.attributes["effect"] == "off"

    # test turn on with useless effect
    # it should send a effect in the request if the device has no effect active
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id, "effect": "off"},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 9
    assert "effects" not in mock_bridge_v2.mock_requests[8]["json"]

    # test timed effect
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id, "effect": "sunrise", "transition": 6},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 10
    assert (
        mock_bridge_v2.mock_requests[9]["json"]["timed_effects"]["effect"] == "sunrise"
    )
    assert mock_bridge_v2.mock_requests[9]["json"]["timed_effects"]["duration"] == 6000

    # test enabling effect should ignore color temperature
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id, "effect": "candle", "color_temp_kelvin": 2000},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 11
    assert mock_bridge_v2.mock_requests[10]["json"]["effects"]["effect"] == "candle"
    assert "color_temperature" not in mock_bridge_v2.mock_requests[10]["json"]

    # test enabling effect should ignore xy color
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id, "effect": "candle", "xy_color": [0.123, 0.123]},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 12
    assert mock_bridge_v2.mock_requests[11]["json"]["effects"]["effect"] == "candle"
    assert "xy_color" not in mock_bridge_v2.mock_requests[11]["json"]