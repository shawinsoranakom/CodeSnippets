async def test_device_trackers(
    hass: HomeAssistant, mock_device_registry_devices
) -> None:
    """Test device_trackers created by mikrotik."""

    # test devices are added from wireless list only
    await setup_mikrotik_entry(hass)

    device_1 = hass.states.get("device_tracker.device_1")
    assert device_1
    assert device_1.state == "home"
    assert device_1.attributes["ip"] == "0.0.0.1"
    assert device_1.attributes["mac"] == "00:00:00:00:00:01"
    assert device_1.attributes["host_name"] == "Device_1"
    device_2 = hass.states.get("device_tracker.device_2")
    assert device_2 is None

    with patch.object(mikrotik.coordinator.MikrotikData, "command", new=mock_command):
        # test device_2 is added after connecting to wireless network
        WIRELESS_DATA.append(DEVICE_2_WIRELESS)

        async_fire_time_changed(hass, utcnow() + timedelta(seconds=10))
        await hass.async_block_till_done(wait_background_tasks=True)

        device_2 = hass.states.get("device_tracker.device_2")
        assert device_2
        assert device_2.state == "home"
        assert device_2.attributes["ip"] == "0.0.0.2"
        assert device_2.attributes["mac"] == "00:00:00:00:00:02"
        assert device_2.attributes["host_name"] == "Device_2"

        # test state remains home if last_seen within consider_home_interval
        del WIRELESS_DATA[1]  # device 2 is removed from wireless list
        with freeze_time(utcnow() + timedelta(minutes=4)):
            async_fire_time_changed(hass, utcnow() + timedelta(minutes=4))
            await hass.async_block_till_done(wait_background_tasks=True)

        device_2 = hass.states.get("device_tracker.device_2")
        assert device_2
        assert device_2.state == "home"

        # test state changes to away if last_seen past consider_home_interval
        with freeze_time(utcnow() + timedelta(minutes=6)):
            async_fire_time_changed(hass, utcnow() + timedelta(minutes=6))
            await hass.async_block_till_done(wait_background_tasks=True)

        device_2 = hass.states.get("device_tracker.device_2")
        assert device_2
        assert device_2.state == "not_home"