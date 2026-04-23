async def test_home_accessory(hass: HomeAssistant, hk_driver) -> None:
    """Test HomeAccessory class."""
    entity_id = "sensor.accessory"
    entity_id2 = "light.accessory_that_exceeds_the_maximum_maximum_maximum_maximum_maximum_maximum_maximum_allowed_length"

    hass.states.async_set(entity_id, None)
    hass.states.async_set(entity_id2, STATE_UNAVAILABLE)

    await hass.async_block_till_done()

    acc = HomeAccessory(
        hass, hk_driver, "Home Accessory", entity_id, 2, {"platform": "isy994"}
    )
    assert acc.hass == hass
    assert acc.display_name == "Home Accessory"
    assert acc.aid == 2
    assert acc.available is True
    assert acc.category == 1  # Category.OTHER
    assert len(acc.services) == 1
    serv = acc.services[0]  # SERV_ACCESSORY_INFO
    assert serv.display_name == SERV_ACCESSORY_INFO
    assert serv.get_characteristic(CHAR_NAME).value == "Home Accessory"
    assert serv.get_characteristic(CHAR_MANUFACTURER).value == "Isy994"
    assert serv.get_characteristic(CHAR_MODEL).value == "Sensor"
    assert serv.get_characteristic(CHAR_SERIAL_NUMBER).value == "sensor.accessory"

    acc2 = HomeAccessory(hass, hk_driver, "Home Accessory", entity_id2, 3, {})
    serv = acc2.services[0]  # SERV_ACCESSORY_INFO
    assert serv.get_characteristic(CHAR_NAME).value == "Home Accessory"
    assert serv.get_characteristic(CHAR_MANUFACTURER).value == f"{MANUFACTURER} Light"
    assert serv.get_characteristic(CHAR_MODEL).value == "Light"
    assert (
        serv.get_characteristic(CHAR_SERIAL_NUMBER).value
        == "light.accessory_that_exceeds_the_maximum_maximum_maximum_maximum"
    )

    acc3 = HomeAccessory(
        hass,
        hk_driver,
        "Home Accessory that exceeds the maximum maximum maximum maximum maximum maximum length",
        entity_id2,
        4,
        {
            ATTR_MODEL: "Awesome Model that exceeds the maximum maximum maximum maximum maximum maximum length",
            ATTR_MANUFACTURER: "Lux Brands that exceeds the maximum maximum maximum maximum maximum maximum length",
            ATTR_SW_VERSION: "0.4.3 that exceeds the maximum maximum maximum maximum maximum maximum length",
            ATTR_INTEGRATION: "luxe that exceeds the maximum maximum maximum maximum maximum maximum length",
        },
    )
    assert acc3.available is False
    serv = acc3.services[0]  # SERV_ACCESSORY_INFO
    assert (
        serv.get_characteristic(CHAR_NAME).value
        == "Home Accessory that exceeds the maximum maximum maximum maximum"
    )
    assert (
        serv.get_characteristic(CHAR_MANUFACTURER).value
        == "Lux Brands that exceeds the maximum maximum maximum maximum maxi"
    )
    assert (
        serv.get_characteristic(CHAR_MODEL).value
        == "Awesome Model that exceeds the maximum maximum maximum maximum m"
    )
    assert (
        serv.get_characteristic(CHAR_SERIAL_NUMBER).value
        == "light.accessory_that_exceeds_the_maximum_maximum_maximum_maximum"
    )
    assert serv.get_characteristic(CHAR_FIRMWARE_REVISION).value == "0.4.3"

    acc4 = HomeAccessory(
        hass,
        hk_driver,
        "Home Accessory that exceeds the maximum maximum maximum maximum maximum maximum length",
        entity_id2,
        5,
        {
            ATTR_MODEL: "Awesome Model that exceeds the maximum maximum maximum maximum maximum maximum length",
            ATTR_MANUFACTURER: "Lux Brands that exceeds the maximum maximum maximum maximum maximum maximum length",
            ATTR_SW_VERSION: "will_not_match_regex",
            ATTR_INTEGRATION: "luxe that exceeds the maximum maximum maximum maximum maximum maximum length",
        },
    )
    assert acc4.available is False
    serv = acc4.services[0]  # SERV_ACCESSORY_INFO
    assert (
        serv.get_characteristic(CHAR_NAME).value
        == "Home Accessory that exceeds the maximum maximum maximum maximum"
    )
    assert (
        serv.get_characteristic(CHAR_MANUFACTURER).value
        == "Lux Brands that exceeds the maximum maximum maximum maximum maxi"
    )
    assert (
        serv.get_characteristic(CHAR_MODEL).value
        == "Awesome Model that exceeds the maximum maximum maximum maximum m"
    )
    assert (
        serv.get_characteristic(CHAR_SERIAL_NUMBER).value
        == "light.accessory_that_exceeds_the_maximum_maximum_maximum_maximum"
    )
    assert format_version(hass_version).startswith(
        serv.get_characteristic(CHAR_FIRMWARE_REVISION).value
    )

    hass.states.async_set(entity_id, "on")
    await hass.async_block_till_done()
    with patch(
        "homeassistant.components.homekit.accessories.HomeAccessory.async_update_state"
    ) as mock_async_update_state:
        acc.run()
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        mock_async_update_state.assert_called_with(state)

        hass.states.async_remove(entity_id)
        await hass.async_block_till_done()
        assert mock_async_update_state.call_count == 1

    with pytest.raises(NotImplementedError):
        acc.async_update_state("new_state")

    # Test model name from domain
    entity_id = "test_model.demo"
    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()
    acc = HomeAccessory(hass, hk_driver, "test_name", entity_id, 6, None)
    serv = acc.services[0]  # SERV_ACCESSORY_INFO
    assert serv.get_characteristic(CHAR_MODEL).value == "Test Model"