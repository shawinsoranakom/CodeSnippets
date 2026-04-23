async def test_discover_lights(hass: HomeAssistant, hue_client: TestClient) -> None:
    """Test the discovery of lights."""
    result = await hue_client.get("/api/username/lights")

    assert result.status == HTTPStatus.OK
    assert CONTENT_TYPE_JSON in result.headers["content-type"]

    result_json = await result.json()

    devices = {val["uniqueid"] for val in result_json.values()}

    # Make sure the lights we added to the config are there
    assert "00:2f:d2:31:ce:c5:55:cc-ee" in devices  # light.ceiling_lights
    assert "00:b6:14:77:34:b7:bb:06-e8" not in devices  # light.bed_light
    assert "00:95:b7:51:16:58:6c:c0-c5" in devices  # script.set_kitchen_light
    assert "00:64:7b:e4:96:c3:fe:90-c3" not in devices  # light.kitchen_lights
    assert "00:7e:8a:42:35:66:db:86-c5" in devices  # media_player.living_room
    assert "00:05:44:c2:d6:0a:e5:17-b7" in devices  # media_player.bedroom
    assert "00:f3:5f:fa:31:f3:32:21-a8" in devices  # media_player.walkman
    assert "00:b4:06:2e:91:95:23:97-fb" in devices  # media_player.lounge_room
    assert "00:b2:bd:f9:2c:ad:22:ae-58" in devices  # fan.living_room_fan
    assert "00:77:4c:8a:23:7d:27:4b-7f" not in devices  # fan.ceiling_fan
    assert "00:02:53:b9:d5:1a:b3:67-b2" in devices  # cover.living_room_window
    assert "00:42:03:fe:97:58:2d:b1-50" in devices  # climate.hvac
    assert "00:7b:2a:c7:08:d6:66:bf-80" in devices  # climate.heatpump
    assert "00:57:77:a1:6a:8e:ef:b3-6c" not in devices  # climate.ecobee
    assert "00:18:7c:7e:78:0e:cd:86-ae" in devices  # light.no_brightness
    assert "00:78:eb:f8:d5:0c:14:85-e7" in devices  # humidifier.humidifier
    assert "00:67:19:bd:ea:e4:2d:ef-22" in devices  # humidifier.dehumidifier
    assert "00:61:bf:ab:08:b1:a6:18-43" not in devices  # humidifier.hygrostat
    assert "00:62:5c:3e:df:58:40:01-43" in devices  # scene.light_on
    assert "00:1c:72:08:ed:09:e7:89-77" in devices  # scene.light_off

    # Remove the state and ensure it disappears from devices
    hass.states.async_remove("light.ceiling_lights")
    await hass.async_block_till_done()

    result_json = await async_get_lights(hue_client)
    assert "1" not in result_json
    devices = {val["uniqueid"] for val in result_json.values()}
    assert "00:2f:d2:31:ce:c5:55:cc-ee" not in devices  # light.ceiling_lights

    # Restore the state and ensure it reappears in devices
    hass.states.async_set("light.ceiling_lights", STATE_ON)
    await hass.async_block_till_done()
    result_json = await async_get_lights(hue_client)
    device = result_json["1"]  # Test that light ID did not change
    assert device["uniqueid"] == "00:2f:d2:31:ce:c5:55:cc-ee"  # light.ceiling_lights
    assert device["state"][HUE_API_STATE_ON] is True

    # Test that returned value is fresh and not cached
    hass.states.async_set("light.ceiling_lights", STATE_OFF)
    await hass.async_block_till_done()
    result_json = await async_get_lights(hue_client)
    device = result_json["1"]
    assert device["state"][HUE_API_STATE_ON] is False