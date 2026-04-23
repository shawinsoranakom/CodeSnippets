async def test_adapter_scanner_fails_to_start_first_time(hass: HomeAssistant) -> None:
    """Test we can recover when the adapter stops responding and the first recovery fails."""

    called_start = 0
    called_stop = 0
    _callback = None
    mock_discovered = []

    class MockBleakScanner:
        async def start(self, *args, **kwargs):
            """Mock Start."""
            nonlocal called_start
            called_start += 1
            if called_start == 1:
                return  # Start ok the first time
            if called_start < 4:
                raise BleakError("Failed to start")

        async def stop(self, *args, **kwargs):
            """Mock Start."""
            nonlocal called_stop
            called_stop += 1

        @property
        def discovered_devices(self):
            """Mock discovered_devices."""
            nonlocal mock_discovered
            return mock_discovered

        def register_detection_callback(self, callback: AdvertisementDataCallback):
            """Mock Register Detection Callback."""
            nonlocal _callback
            _callback = callback

    scanner = MockBleakScanner()
    start_time_monotonic = time.monotonic()

    with (
        patch_bluetooth_time(
            start_time_monotonic,
        ),
        patch(
            "habluetooth.scanner.OriginalBleakScanner",
            return_value=scanner,
        ),
    ):
        await async_setup_with_one_adapter(hass)

        assert called_start == 1

        mock_discovered = [MagicMock()]

        # Ensure we don't restart the scanner if we don't need to
        with patch_bluetooth_time(
            start_time_monotonic + 10,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        assert called_start == 1

        # Ensure we don't restart the scanner if we don't need to
        with patch_bluetooth_time(
            start_time_monotonic + 20,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        assert called_start == 1

        # We hit the timer with no detections, so we reset the adapter and restart the scanner
        with (
            patch_bluetooth_time(
                start_time_monotonic
                + SCANNER_WATCHDOG_TIMEOUT
                + SCANNER_WATCHDOG_INTERVAL.total_seconds(),
            ),
            patch(
                "habluetooth.util.recover_adapter", return_value=True
            ) as mock_recover_adapter,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        assert len(mock_recover_adapter.mock_calls) == 1
        assert called_start == 4

        now_monotonic = time.monotonic()
        # We hit the timer again the previous start call failed, make sure
        # we try again
        with (
            patch_bluetooth_time(
                now_monotonic
                + SCANNER_WATCHDOG_TIMEOUT * 2
                + SCANNER_WATCHDOG_INTERVAL.total_seconds(),
            ),
            patch(
                "habluetooth.util.recover_adapter", return_value=True
            ) as mock_recover_adapter,
        ):
            async_fire_time_changed(hass, dt_util.utcnow() + SCANNER_WATCHDOG_INTERVAL)
            await hass.async_block_till_done()

        assert len(mock_recover_adapter.mock_calls) == 1
        assert called_start == 5