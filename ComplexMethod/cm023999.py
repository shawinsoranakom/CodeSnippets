async def test_unavailable_after_no_data(hass: HomeAssistant) -> None:
    """Test that the coordinator is unavailable after no data for a while."""
    start_monotonic = time.monotonic()

    with patch(
        "bleak.BleakScanner.discovered_devices_and_advertisement_data",  # Must patch before we setup
        {"44:44:33:11:23:45": (MagicMock(address="44:44:33:11:23:45"), MagicMock())},
    ):
        await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
        await hass.async_block_till_done()

    @callback
    def _mock_update_method(
        service_info: BluetoothServiceInfo,
    ) -> dict[str, str]:
        return {"test": "data"}

    @callback
    def _async_generate_mock_data(
        data: dict[str, str],
    ) -> PassiveBluetoothDataUpdate:
        """Generate mock data."""
        return GENERIC_PASSIVE_BLUETOOTH_DATA_UPDATE

    coordinator = PassiveBluetoothProcessorCoordinator(
        hass,
        _LOGGER,
        "aa:bb:cc:dd:ee:ff",
        BluetoothScanningMode.ACTIVE,
        _mock_update_method,
    )
    assert coordinator.available is False  # no data yet

    processor = PassiveBluetoothDataProcessor(_async_generate_mock_data)

    unregister_processor = coordinator.async_register_processor(processor)
    cancel_coordinator = coordinator.async_start()

    mock_entity = MagicMock()
    mock_add_entities = MagicMock()
    processor.async_add_entities_listener(
        mock_entity,
        mock_add_entities,
    )

    assert coordinator.available is False
    assert processor.available is False

    now = time.monotonic()
    service_info_at_time = BluetoothServiceInfoBleak(
        name="Generic",
        address="aa:bb:cc:dd:ee:ff",
        rssi=-95,
        manufacturer_data={
            1: b"\x01\x01\x01\x01\x01\x01\x01\x01",
        },
        service_data={},
        service_uuids=[],
        source="local",
        time=now,
        device=MagicMock(),
        advertisement=MagicMock(),
        connectable=True,
        tx_power=0,
    )

    inject_bluetooth_service_info_bleak(hass, service_info_at_time)
    assert len(mock_add_entities.mock_calls) == 1
    assert coordinator.available is True
    assert processor.available is True
    monotonic_now = start_monotonic + FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1

    with (
        patch_bluetooth_time(
            monotonic_now,
        ),
        patch_all_discovered_devices([MagicMock(address="44:44:33:11:23:45")]),
    ):
        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=UNAVAILABLE_TRACK_SECONDS)
        )
        await hass.async_block_till_done()
    assert coordinator.available is False
    assert processor.available is False
    assert coordinator.last_seen == service_info_at_time.time

    inject_bluetooth_service_info_bleak(hass, service_info_at_time)
    assert len(mock_add_entities.mock_calls) == 1
    assert coordinator.available is True
    assert processor.available is True

    monotonic_now = start_monotonic + FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 2

    with (
        patch_bluetooth_time(
            monotonic_now,
        ),
        patch_all_discovered_devices([MagicMock(address="44:44:33:11:23:45")]),
    ):
        async_fire_time_changed(
            hass, dt_util.utcnow() + timedelta(seconds=UNAVAILABLE_TRACK_SECONDS)
        )
        await hass.async_block_till_done()
    assert coordinator.available is False
    assert processor.available is False
    assert coordinator.last_seen == service_info_at_time.time

    unregister_processor()
    cancel_coordinator()