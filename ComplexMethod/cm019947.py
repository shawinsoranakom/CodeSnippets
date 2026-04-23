async def test_reproducing_states(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test reproducing Light states."""
    hass.states.async_set("light.entity_off", "off", {})
    hass.states.async_set("light.entity_bright", "on", VALID_BRIGHTNESS)
    hass.states.async_set("light.entity_effect", "on", VALID_EFFECT)
    hass.states.async_set("light.entity_temp", "on", VALID_COLOR_TEMP_KELVIN)
    hass.states.async_set("light.entity_hs", "on", VALID_HS_COLOR)
    hass.states.async_set("light.entity_rgb", "on", VALID_RGB_COLOR)
    hass.states.async_set("light.entity_xy", "on", VALID_XY_COLOR)

    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    turn_off_calls = async_mock_service(hass, "light", "turn_off")

    # These calls should do nothing as entities already in desired state
    await async_reproduce_state(
        hass,
        [
            State("light.entity_off", "off"),
            State("light.entity_bright", "on", VALID_BRIGHTNESS),
            State("light.entity_effect", "on", VALID_EFFECT),
            State("light.entity_temp", "on", VALID_COLOR_TEMP_KELVIN),
            State("light.entity_hs", "on", VALID_HS_COLOR),
            State("light.entity_rgb", "on", VALID_RGB_COLOR),
            State("light.entity_xy", "on", VALID_XY_COLOR),
        ],
    )

    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0

    # Test invalid state is handled
    await async_reproduce_state(hass, [State("light.entity_off", "not_supported")])

    assert "not_supported" in caplog.text
    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0

    # Make sure correct services are called
    await async_reproduce_state(
        hass,
        [
            State("light.entity_xy", "off"),
            State("light.entity_off", "on", VALID_BRIGHTNESS),
            State("light.entity_bright", "on", VALID_EFFECT),
            State("light.entity_effect", "on", VALID_COLOR_TEMP_KELVIN),
            State("light.entity_temp", "on", VALID_HS_COLOR),
            State("light.entity_hs", "on", VALID_RGB_COLOR),
            State("light.entity_rgb", "on", VALID_XY_COLOR),
        ],
    )

    assert len(turn_on_calls) == 6

    expected_calls = []

    expected_off = dict(VALID_BRIGHTNESS)
    expected_off["entity_id"] = "light.entity_off"
    expected_calls.append(expected_off)

    expected_bright = dict(VALID_EFFECT)
    expected_bright["entity_id"] = "light.entity_bright"
    expected_calls.append(expected_bright)

    expected_effect = dict(VALID_COLOR_TEMP_KELVIN)
    expected_effect["entity_id"] = "light.entity_effect"
    expected_calls.append(expected_effect)

    expected_temp = dict(VALID_HS_COLOR)
    expected_temp["entity_id"] = "light.entity_temp"
    expected_calls.append(expected_temp)

    expected_hs = dict(VALID_RGB_COLOR)
    expected_hs["entity_id"] = "light.entity_hs"
    expected_calls.append(expected_hs)

    expected_rgb = dict(VALID_XY_COLOR)
    expected_rgb["entity_id"] = "light.entity_rgb"
    expected_calls.append(expected_rgb)

    for call in turn_on_calls:
        assert call.domain == "light"
        found = False
        for expected in expected_calls:
            if call.data["entity_id"] == expected["entity_id"]:
                # We found the matching entry
                assert call.data == expected
                found = True
                break
        # No entry found
        assert found

    assert len(turn_off_calls) == 1
    assert turn_off_calls[0].domain == "light"
    assert turn_off_calls[0].data == {"entity_id": "light.entity_xy"}