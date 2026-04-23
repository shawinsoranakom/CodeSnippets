async def test_accessory_with_hardware_revision(hass: HomeAssistant, hk_driver) -> None:
    """Test HomeAccessory class with hardware revision."""
    entity_id = "sensor.accessory"
    hass.states.async_set(entity_id, "on")
    acc = HomeAccessory(
        hass,
        hk_driver,
        "Home Accessory",
        entity_id,
        3,
        {
            ATTR_MODEL: None,
            ATTR_MANUFACTURER: None,
            ATTR_SW_VERSION: None,
            ATTR_HW_VERSION: "1.2.3",
            ATTR_INTEGRATION: None,
        },
    )
    acc.driver = hk_driver
    serv = acc.get_service(SERV_ACCESSORY_INFO)
    assert serv.get_characteristic(CHAR_NAME).value == "Home Accessory"
    assert serv.get_characteristic(CHAR_MANUFACTURER).value == "Home Assistant Sensor"
    assert serv.get_characteristic(CHAR_MODEL).value == "Sensor"
    assert serv.get_characteristic(CHAR_SERIAL_NUMBER).value == entity_id
    assert format_version(hass_version).startswith(
        serv.get_characteristic(CHAR_FIRMWARE_REVISION).value
    )
    assert serv.get_characteristic(CHAR_HARDWARE_REVISION).value == "1.2.3"
    assert isinstance(acc.to_HAP(), dict)