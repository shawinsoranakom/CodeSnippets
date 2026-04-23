async def test_home(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, router: Mock
) -> None:
    """Test home binary sensors."""
    await setup_platform(hass, BINARY_SENSOR_DOMAIN)

    # Device class
    assert (
        hass.states.get("binary_sensor.detecteur").attributes[ATTR_DEVICE_CLASS]
        == BinarySensorDeviceClass.MOTION
    )
    assert (
        hass.states.get("binary_sensor.ouverture_porte").attributes[ATTR_DEVICE_CLASS]
        == BinarySensorDeviceClass.DOOR
    )
    assert (
        hass.states.get("binary_sensor.ouverture_porte_couvercle").attributes[
            ATTR_DEVICE_CLASS
        ]
        == BinarySensorDeviceClass.SAFETY
    )

    # Initial state
    assert hass.states.get("binary_sensor.detecteur").state == "on"
    assert hass.states.get("binary_sensor.detecteur_couvercle").state == "off"
    assert hass.states.get("binary_sensor.ouverture_porte").state == "unknown"
    assert hass.states.get("binary_sensor.ouverture_porte_couvercle").state == "off"

    # Now simulate a changed status
    data_home_get_values_changed = deepcopy(DATA_HOME_PIR_GET_VALUE)
    data_home_get_values_changed["value"] = True
    router().home.get_home_endpoint_value.return_value = data_home_get_values_changed

    # Simulate an update
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.detecteur").state == "off"
    assert hass.states.get("binary_sensor.detecteur_couvercle").state == "on"
    assert hass.states.get("binary_sensor.ouverture_porte").state == "off"
    assert hass.states.get("binary_sensor.ouverture_porte_couvercle").state == "on"