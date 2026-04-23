async def test_light_turn_off_service(
    hass: HomeAssistant, mock_bridge_v2: Mock, v2_resources_test_data: JsonArrayType
) -> None:
    """Test calling the turn off service on a light."""
    await mock_bridge_v2.api.load_test_data(v2_resources_test_data)

    await setup_platform(hass, mock_bridge_v2, Platform.LIGHT)

    test_light_id = "light.hue_light_with_color_and_color_temperature_1"

    # verify the light is on before we start
    assert hass.states.get(test_light_id).state == "on"
    brightness_pct = hass.states.get(test_light_id).attributes["brightness"] / 255 * 100

    # now call the HA turn_off service
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": test_light_id},
        blocking=True,
    )

    # PUT request should have been sent to device with correct params
    assert len(mock_bridge_v2.mock_requests) == 1
    assert mock_bridge_v2.mock_requests[0]["method"] == "put"
    assert mock_bridge_v2.mock_requests[0]["json"]["on"]["on"] is False

    # Now generate update event by emitting the json we've sent as incoming event
    event = {
        "id": "02cba059-9c2c-4d45-97e4-4f79b1bfbaa1",
        "type": "light",
        **mock_bridge_v2.mock_requests[0]["json"],
    }
    mock_bridge_v2.api.emit_event("update", event)
    await hass.async_block_till_done()

    # the light should now be off
    test_light = hass.states.get(test_light_id)
    assert test_light is not None
    assert test_light.state == "off"

    # test again with sending transition
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": test_light_id, "transition": 0.25},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 2
    assert mock_bridge_v2.mock_requests[1]["json"]["on"]["on"] is False
    assert mock_bridge_v2.mock_requests[1]["json"]["dynamics"]["duration"] == 200

    # test turn_on resets brightness
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": test_light_id},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 3
    assert mock_bridge_v2.mock_requests[2]["json"]["on"]["on"] is True
    assert (
        round(
            mock_bridge_v2.mock_requests[2]["json"]["dimming"]["brightness"]
            - brightness_pct
        )
        == 0
    )

    # test again with sending long flash
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": test_light_id, "flash": "long"},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 4
    assert mock_bridge_v2.mock_requests[3]["json"]["alert"]["action"] == "breathe"

    # test again with sending short flash
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": test_light_id, "flash": "short"},
        blocking=True,
    )
    assert len(mock_bridge_v2.mock_requests) == 5
    assert mock_bridge_v2.mock_requests[4]["json"]["identify"]["action"] == "identify"