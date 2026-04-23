async def test_advertisment_interval_longer_than_adapter_stack_timeout_adapter_change_not_connectable(
    hass: HomeAssistant,
) -> None:
    """Test device with a long advertisement interval with an adapter change that is not connectable."""
    start_monotonic_time = time.monotonic()
    switchbot_device = generate_ble_device("44:44:33:11:23:45", "wohand")
    switchbot_adv = generate_advertisement_data(
        local_name="wohand",
        service_uuids=["cba20d00-224d-11e6-9fb8-0002a5d5c51b"],
        rssi=-100,
    )
    switchbot_device_went_unavailable = False

    scanner = FakeScanner("new", "fake_adapter")
    cancel_scanner = async_register_scanner(hass, scanner)

    @callback
    def _switchbot_device_unavailable_callback(_address: str) -> None:
        """Switchbot device unavailable callback."""
        nonlocal switchbot_device_went_unavailable
        switchbot_device_went_unavailable = True

    for i in range(ADVERTISING_TIMES_NEEDED):
        inject_advertisement_with_time_and_source_connectable(
            hass,
            switchbot_device,
            switchbot_adv,
            start_monotonic_time + (i * 2),
            "original",
            connectable=False,
        )

    assert async_get_learned_advertising_interval(
        hass, "44:44:33:11:23:45"
    ) == pytest.approx(2.0)

    switchbot_better_rssi_adv = generate_advertisement_data(
        local_name="wohand",
        service_uuids=["cba20d00-224d-11e6-9fb8-0002a5d5c51b"],
        rssi=-30,
    )
    for i in range(ADVERTISING_TIMES_NEEDED):
        inject_advertisement_with_time_and_source_connectable(
            hass,
            switchbot_device,
            switchbot_better_rssi_adv,
            start_monotonic_time + (i * ONE_HOUR_SECONDS),
            "new",
            connectable=False,
        )

    assert async_get_learned_advertising_interval(
        hass, "44:44:33:11:23:45"
    ) == pytest.approx(ONE_HOUR_SECONDS)

    switchbot_device_unavailable_cancel = async_track_unavailable(
        hass,
        _switchbot_device_unavailable_callback,
        switchbot_device.address,
        connectable=False,
    )

    monotonic_now = start_monotonic_time + (
        (ADVERTISING_TIMES_NEEDED - 1) * ONE_HOUR_SECONDS
    )
    with patch_bluetooth_time(
        monotonic_now + UNAVAILABLE_TRACK_SECONDS,
    ):
        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=UNAVAILABLE_TRACK_SECONDS)
        )
        await hass.async_block_till_done()

    assert switchbot_device_went_unavailable is False
    cancel_scanner()

    # Now that the scanner is gone we should go back to the stack default timeout
    with patch_bluetooth_time(
        monotonic_now + UNAVAILABLE_TRACK_SECONDS,
    ):
        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=UNAVAILABLE_TRACK_SECONDS)
        )
        await hass.async_block_till_done()

    assert switchbot_device_went_unavailable is False

    # Now that the scanner is gone we should go back to the stack default timeout
    with patch_bluetooth_time(
        monotonic_now + UNAVAILABLE_TRACK_SECONDS,
    ):
        async_fire_time_changed(
            hass,
            dt_util.utcnow()
            + timedelta(seconds=FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS),
        )
        await hass.async_block_till_done()

    assert switchbot_device_went_unavailable is False

    switchbot_device_unavailable_cancel()