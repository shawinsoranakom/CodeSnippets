async def test_non_color_light_reports_color(
    hass: HomeAssistant,
    light_ws_data: WebsocketDataType,
) -> None:
    """Verify hs_color does not crash when a group gets updated with a bad color value.

    After calling a scene color temp light of certain manufacturers
    report color temp in color space.
    """
    assert len(hass.states.async_all()) == 3
    assert hass.states.get("light.group").attributes[ATTR_SUPPORTED_COLOR_MODES] == [
        ColorMode.COLOR_TEMP,
        ColorMode.HS,
        ColorMode.XY,
    ]
    assert (
        hass.states.get("light.group").attributes[ATTR_COLOR_MODE]
        == ColorMode.COLOR_TEMP
    )
    assert hass.states.get("light.group").attributes[ATTR_COLOR_TEMP_KELVIN] == 4000

    # Updating a scene will return a faulty color value
    # for a non-color light causing an exception in hs_color
    event_changed_light = {
        "id": "1",
        "state": {
            "alert": None,
            "bri": 216,
            "colormode": "xy",
            "ct": 410,
            "on": True,
            "reachable": True,
        },
        "uniqueid": "ec:1b:bd:ff:fe:ee:ed:dd-01",
    }
    await light_ws_data(event_changed_light)
    group = hass.states.get("light.group")
    assert group.attributes[ATTR_COLOR_MODE] == ColorMode.XY
    assert group.attributes[ATTR_HS_COLOR] == (40.571, 41.176)
    assert group.attributes.get(ATTR_COLOR_TEMP_KELVIN) is None