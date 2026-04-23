async def test_coordinator_stale_device_serial_bridge(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_serial_bridge: AsyncMock,
    mock_serial_bridge_config_entry: MockConfigEntry,
) -> None:
    """Test coordinator data update removes stale Serial Brdige devices."""

    entity_id_0 = "light.light0"
    entity_id_1 = "light.light1"

    mock_serial_bridge.get_all_devices.return_value = {
        CLIMATE: {},
        COVER: {},
        LIGHT: {
            0: LIGHT0,
            1: ComelitSerialBridgeObject(
                index=1,
                name="Light1",
                status=0,
                human_status="off",
                type="light",
                val=0,
                protected=0,
                zone="Bathroom",
                power=0.0,
                power_unit=WATT,
            ),
        },
        OTHER: {},
        IRRIGATION: {},
        SCENARIO: {},
    }

    await setup_integration(hass, mock_serial_bridge_config_entry)

    assert (state := hass.states.get(entity_id_0))
    assert state.state == STATE_OFF
    assert (state := hass.states.get(entity_id_1))
    assert state.state == STATE_OFF

    mock_serial_bridge.get_all_devices.return_value = {
        CLIMATE: {},
        COVER: {},
        LIGHT: {0: LIGHT0},
        OTHER: {},
        IRRIGATION: {},
        SCENARIO: {},
    }

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id_0))
    assert state.state == STATE_OFF

    # Light1 is removed
    assert not hass.states.get(entity_id_1)