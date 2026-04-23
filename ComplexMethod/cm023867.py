async def test_light_without_brightness_can_be_turned_on(
    hass_hue: HomeAssistant, hue_client: TestClient
) -> None:
    """Test that light without brightness can be turned on."""
    hass_hue.states.async_set("light.no_brightness", "off", {})

    # Check if light can be turned on
    turn_on_calls = []

    @callback
    def mock_service_call(call):
        """Mock service call."""
        turn_on_calls.append(call)
        hass_hue.states.async_set("light.no_brightness", "on", {})

    hass_hue.services.async_register(
        light.DOMAIN, SERVICE_TURN_ON, mock_service_call, schema=None
    )

    no_brightness_result = await perform_put_light_state(
        hass_hue,
        hue_client,
        "light.no_brightness",
        True,
        # Some remotes, like HarmonyHub send brightness value regardless of light's features
        brightness=0,
    )

    no_brightness_result_json = await no_brightness_result.json()

    assert no_brightness_result.status == HTTPStatus.OK
    assert CONTENT_TYPE_JSON in no_brightness_result.headers["content-type"]
    assert len(no_brightness_result_json) == 1

    # Verify that SERVICE_TURN_ON has been called
    await hass_hue.async_block_till_done()
    assert len(turn_on_calls) == 1
    call = turn_on_calls[-1]

    assert call.domain == light.DOMAIN
    assert call.service == SERVICE_TURN_ON
    assert "light.no_brightness" in call.data[ATTR_ENTITY_ID]