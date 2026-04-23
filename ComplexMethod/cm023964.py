async def test_delay(
    hass: HomeAssistant, mock_pymodbus, freezer: FrozenDateTimeFactory
) -> None:
    """Run test for startup delay."""

    # the purpose of this test is to test startup delay
    # We "hijiack" a binary_sensor to make a proper blackbox test.
    set_delay = 15
    set_scan_interval = 5
    entity_id = f"{BINARY_SENSOR_DOMAIN}.{TEST_ENTITY_NAME}".replace(" ", "_")
    config = {
        DOMAIN: [
            {
                CONF_TYPE: TCP,
                CONF_HOST: TEST_MODBUS_HOST,
                CONF_PORT: TEST_PORT_TCP,
                CONF_NAME: TEST_MODBUS_NAME,
                CONF_DELAY: set_delay,
                CONF_BINARY_SENSORS: [
                    {
                        CONF_INPUT_TYPE: CALL_TYPE_COIL,
                        CONF_NAME: TEST_ENTITY_NAME,
                        CONF_ADDRESS: 52,
                        CONF_SLAVE: 0,
                        CONF_SCAN_INTERVAL: set_scan_interval,
                    },
                ],
            }
        ]
    }
    mock_pymodbus.read_coils.return_value = ReadResult([0x01])
    start_time = dt_util.utcnow()
    assert await async_setup_component(hass, DOMAIN, config) is True
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state in (STATE_UNKNOWN, STATE_UNAVAILABLE)

    time_sensor_active = start_time + timedelta(seconds=2)
    time_after_delay = start_time + timedelta(seconds=(set_delay))
    time_after_scan = time_after_delay + timedelta(seconds=(set_scan_interval))
    time_stop = time_after_scan + timedelta(seconds=10)
    now = start_time
    while now < time_stop:
        # This test assumed listeners are always fired at 0
        # microseconds which is impossible in production so
        # we use 999999 microseconds to simulate the real world.
        freezer.tick(timedelta(seconds=1, microseconds=999999))
        now = dt_util.utcnow()
        async_fire_time_changed(hass, now)
        await hass.async_block_till_done()
        if now > time_sensor_active:
            if now <= time_after_delay:
                assert hass.states.get(entity_id).state in (
                    STATE_UNKNOWN,
                    STATE_UNAVAILABLE,
                )
            if now <= time_after_delay + timedelta(seconds=2):
                continue
            if now > time_after_scan + timedelta(seconds=2):
                assert hass.states.get(entity_id).state == STATE_ON