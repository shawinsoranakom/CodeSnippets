async def test_async_current_scanners(hass: HomeAssistant) -> None:
    """Test getting the list of current scanners."""
    # The enable_bluetooth fixture registers one scanner
    initial_scanners = bluetooth.async_current_scanners(hass)
    assert len(initial_scanners) == 1
    initial_scanner_count = len(initial_scanners)

    # Verify current_mode is accessible on the initial scanner
    for scanner in initial_scanners:
        assert hasattr(scanner, "current_mode")
        # The mode might be None or a BluetoothScanningMode enum value

    # Register additional connectable scanners
    hci0_scanner = FakeScanner("hci0", "hci0")
    hci1_scanner = FakeScanner("hci1", "hci1")
    cancel_hci0 = bluetooth.async_register_scanner(hass, hci0_scanner)
    cancel_hci1 = bluetooth.async_register_scanner(hass, hci1_scanner)

    # Test that the new scanners are added
    scanners = bluetooth.async_current_scanners(hass)
    assert len(scanners) == initial_scanner_count + 2
    assert hci0_scanner in scanners
    assert hci1_scanner in scanners

    # Verify current_mode is accessible on all scanners
    for scanner in scanners:
        assert hasattr(scanner, "current_mode")
        # Verify it's None or the correct type (BluetoothScanningMode)
        assert scanner.current_mode is None or isinstance(
            scanner.current_mode, BluetoothScanningMode
        )

    # Register non-connectable scanner
    connector = HaBluetoothConnector(
        MockBleakClient, "mock_bleak_client", lambda: False
    )
    hci2_scanner = FakeRemoteScanner("hci2", "hci2", connector, False)
    cancel_hci2 = bluetooth.async_register_scanner(hass, hci2_scanner)

    # Test that all scanners are returned (both connectable and non-connectable)
    all_scanners = bluetooth.async_current_scanners(hass)
    assert len(all_scanners) == initial_scanner_count + 3
    assert hci0_scanner in all_scanners
    assert hci1_scanner in all_scanners
    assert hci2_scanner in all_scanners

    # Verify current_mode is accessible on all scanners including non-connectable
    for scanner in all_scanners:
        assert hasattr(scanner, "current_mode")
        # The mode should be None or a BluetoothScanningMode instance
        assert scanner.current_mode is None or isinstance(
            scanner.current_mode, BluetoothScanningMode
        )

    # Clean up our scanners
    cancel_hci0()
    cancel_hci1()
    cancel_hci2()

    # Verify we're back to the initial scanner
    final_scanners = bluetooth.async_current_scanners(hass)
    assert len(final_scanners) == initial_scanner_count