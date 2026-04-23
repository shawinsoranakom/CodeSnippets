async def test_coordinator_stale_device_vedo(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_vedo: AsyncMock,
    mock_vedo_config_entry: MockConfigEntry,
) -> None:
    """Test coordinator data update removes stale VEDO devices."""

    entity_id_0 = "sensor.zone0"
    entity_id_1 = "sensor.zone1"

    mock_vedo.get_all_areas_and_zones.return_value = {
        ALARM_AREA: {
            0: ComelitVedoAreaObject(
                index=0,
                name="Area0",
                p1=True,
                p2=True,
                ready=False,
                armed=0,
                alarm=False,
                alarm_memory=False,
                sabotage=False,
                anomaly=False,
                in_time=False,
                out_time=False,
                human_status=AlarmAreaState.DISARMED,
            )
        },
        ALARM_ZONE: {
            0: ZONE0,
            1: ComelitVedoZoneObject(
                index=1,
                name="Zone1",
                status_api="0x000",
                status=0,
                human_status=AlarmZoneState.REST,
            ),
        },
    }
    await setup_integration(hass, mock_vedo_config_entry)

    assert (state := hass.states.get(entity_id_0))
    assert state.state == AlarmZoneState.REST.value
    assert (state := hass.states.get(entity_id_1))
    assert state.state == AlarmZoneState.REST.value

    mock_vedo.get_all_areas_and_zones.return_value = {
        ALARM_AREA: {
            0: ComelitVedoAreaObject(
                index=0,
                name="Area0",
                p1=True,
                p2=True,
                ready=False,
                armed=0,
                alarm=False,
                alarm_memory=False,
                sabotage=False,
                anomaly=False,
                in_time=False,
                out_time=False,
                human_status=AlarmAreaState.DISARMED,
            )
        },
        ALARM_ZONE: {
            0: ZONE0,
        },
    }

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id_0))
    assert state.state == AlarmZoneState.REST.value

    # Zone1 is removed
    assert not hass.states.get(entity_id_1)