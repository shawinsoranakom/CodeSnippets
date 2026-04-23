async def test_see_passive_zone_state(
    hass: HomeAssistant,
    mock_device_tracker_conf: list[legacy.Device],
    mock_legacy_device_scanner: MockScanner,
) -> None:
    """Test that the device tracker sets gps for passive trackers."""
    now = dt_util.utcnow()

    register_time = datetime(now.year + 1, 9, 15, 23, tzinfo=dt_util.UTC)
    scan_time = datetime(now.year + 1, 9, 15, 23, 1, tzinfo=dt_util.UTC)

    with assert_setup_component(1, zone.DOMAIN):
        zone_info = {
            "name": "Home",
            "latitude": 1,
            "longitude": 2,
            "radius": 250,
            "passive": False,
        }

        await async_setup_component(hass, zone.DOMAIN, {"zone": zone_info})
        await hass.async_block_till_done()

    mock_legacy_device_scanner.reset()
    mock_legacy_device_scanner.come_home("dev1")

    with (
        patch(
            "homeassistant.components.device_tracker.legacy.dt_util.utcnow",
            return_value=register_time,
        ),
        assert_setup_component(1, device_tracker.DOMAIN),
    ):
        assert await async_setup_component(
            hass,
            device_tracker.DOMAIN,
            {
                device_tracker.DOMAIN: {
                    CONF_PLATFORM: "test",
                    device_tracker.CONF_CONSIDER_HOME: 59,
                }
            },
        )
        await hass.async_block_till_done()

    state = hass.states.get("device_tracker.dev1")
    attrs = state.attributes
    assert state.state == STATE_HOME
    assert state.object_id == "dev1"
    assert state.name == "dev1"
    assert attrs.get("friendly_name") == "dev1"
    assert attrs.get("latitude") == 1
    assert attrs.get("longitude") == 2
    assert attrs.get("gps_accuracy") == 0
    assert attrs.get("source_type") == SourceType.ROUTER

    mock_legacy_device_scanner.leave_home("dev1")

    with patch(
        "homeassistant.components.device_tracker.legacy.dt_util.utcnow",
        return_value=scan_time,
    ):
        async_fire_time_changed(hass, scan_time)
        await hass.async_block_till_done()

    state = hass.states.get("device_tracker.dev1")
    attrs = state.attributes
    assert state.state == STATE_NOT_HOME
    assert state.object_id == "dev1"
    assert state.name == "dev1"
    assert attrs.get("friendly_name") == "dev1"
    assert attrs.get("latitude") is None
    assert attrs.get("longitude") is None
    assert attrs.get("gps_accuracy") is None
    assert attrs.get("source_type") == SourceType.ROUTER