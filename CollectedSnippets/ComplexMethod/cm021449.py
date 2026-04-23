def test_setup_params(hass: HomeAssistant) -> None:
    """Test the initial parameters."""
    state = hass.states.get("update.demo_update_no_install")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_TITLE] == "Awesomesoft Inc."
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"
    assert (
        state.attributes[ATTR_RELEASE_SUMMARY] == "Awesome update, fixing everything!"
    )
    assert state.attributes[ATTR_RELEASE_URL] == "https://www.example.com/release/1.0.1"
    assert (
        state.attributes[ATTR_ENTITY_PICTURE] == "/api/brands/integration/demo/icon.png"
    )

    state = hass.states.get("update.demo_no_update")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_TITLE] == "AdGuard Home"
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.0"
    assert state.attributes[ATTR_RELEASE_SUMMARY] is None
    assert state.attributes[ATTR_RELEASE_URL] is None
    assert (
        state.attributes[ATTR_ENTITY_PICTURE] == "/api/brands/integration/demo/icon.png"
    )

    state = hass.states.get("update.demo_add_on")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_TITLE] == "AdGuard Home"
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.1"
    assert (
        state.attributes[ATTR_RELEASE_SUMMARY] == "Awesome update, fixing everything!"
    )
    assert state.attributes[ATTR_RELEASE_URL] == "https://www.example.com/release/1.0.1"
    assert (
        state.attributes[ATTR_ENTITY_PICTURE] == "/api/brands/integration/demo/icon.png"
    )

    state = hass.states.get("update.demo_living_room_bulb_update")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_TITLE] == "Philips Lamps Firmware"
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.93.3"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.94.2"
    assert state.attributes[ATTR_RELEASE_SUMMARY] == "Added support for effects"
    assert (
        state.attributes[ATTR_RELEASE_URL] == "https://www.example.com/release/1.93.3"
    )
    assert state.attributes[ATTR_DEVICE_CLASS] == UpdateDeviceClass.FIRMWARE
    assert (
        state.attributes[ATTR_ENTITY_PICTURE] == "/api/brands/integration/demo/icon.png"
    )

    state = hass.states.get("update.demo_update_with_progress")
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_TITLE] == "Philips Lamps Firmware"
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.93.3"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.94.2"
    assert state.attributes[ATTR_RELEASE_SUMMARY] == "Added support for effects"
    assert (
        state.attributes[ATTR_RELEASE_URL] == "https://www.example.com/release/1.93.3"
    )
    assert state.attributes[ATTR_DEVICE_CLASS] == UpdateDeviceClass.FIRMWARE
    assert (
        state.attributes[ATTR_ENTITY_PICTURE] == "/api/brands/integration/demo/icon.png"
    )