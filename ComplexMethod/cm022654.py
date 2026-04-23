def test_home_bridge(hk_driver) -> None:
    """Test HomeBridge class."""
    bridge = HomeBridge("hass", hk_driver, BRIDGE_NAME)
    assert bridge.hass == "hass"
    assert bridge.display_name == BRIDGE_NAME
    assert bridge.category == 2  # Category.BRIDGE
    assert len(bridge.services) == 2
    serv = bridge.services[0]  # SERV_ACCESSORY_INFO
    assert serv.display_name == SERV_ACCESSORY_INFO
    assert serv.get_characteristic(CHAR_NAME).value == BRIDGE_NAME
    assert format_version(hass_version).startswith(
        serv.get_characteristic(CHAR_FIRMWARE_REVISION).value
    )
    assert serv.get_characteristic(CHAR_MANUFACTURER).value == MANUFACTURER
    assert serv.get_characteristic(CHAR_MODEL).value == BRIDGE_MODEL
    assert serv.get_characteristic(CHAR_SERIAL_NUMBER).value == BRIDGE_SERIAL_NUMBER