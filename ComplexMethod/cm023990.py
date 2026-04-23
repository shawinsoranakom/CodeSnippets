async def test_async_discovered_device_api(
    hass: HomeAssistant, mock_bleak_scanner_start: MagicMock
) -> None:
    """Test the async_discovered_device API."""
    mock_bt = []
    set_manager(None)
    with (
        patch(
            "homeassistant.components.bluetooth.async_get_bluetooth",
            return_value=mock_bt,
        ),
        patch(
            "bleak.BleakScanner.discovered_devices_and_advertisement_data",  # Must patch before we setup
            {
                "44:44:33:11:23:45": (
                    MagicMock(address="44:44:33:11:23:45"),
                    MagicMock(),
                )
            },
        ),
    ):
        with pytest.raises(RuntimeError, match="BluetoothManager has not been set"):
            assert not bluetooth.async_discovered_service_info(hass)
        with pytest.raises(RuntimeError, match="BluetoothManager has not been set"):
            assert not bluetooth.async_address_present(hass, "44:44:22:22:11:22")
        await async_setup_with_default_adapter(hass)

        with patch.object(hass.config_entries.flow, "async_init"):
            hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
            await hass.async_block_till_done()

            assert len(mock_bleak_scanner_start.mock_calls) == 1

            assert not bluetooth.async_discovered_service_info(hass)

            wrong_device = generate_ble_device("44:44:33:11:23:42", "wrong_name")
            wrong_adv = generate_advertisement_data(
                local_name="wrong_name", service_uuids=[]
            )
            inject_advertisement(hass, wrong_device, wrong_adv)
            switchbot_device = generate_ble_device("44:44:33:11:23:45", "wohand")
            switchbot_adv = generate_advertisement_data(
                local_name="wohand", service_uuids=[]
            )
            inject_advertisement(hass, switchbot_device, switchbot_adv)
            wrong_device_went_unavailable = False
            switchbot_device_went_unavailable = False

            @callback
            def _wrong_device_unavailable_callback(_address: str) -> None:
                """Wrong device unavailable callback."""
                nonlocal wrong_device_went_unavailable
                wrong_device_went_unavailable = True
                raise ValueError("blow up")

            @callback
            def _switchbot_device_unavailable_callback(_address: str) -> None:
                """Switchbot device unavailable callback."""
                nonlocal switchbot_device_went_unavailable
                switchbot_device_went_unavailable = True

            wrong_device_unavailable_cancel = async_track_unavailable(
                hass, _wrong_device_unavailable_callback, wrong_device.address
            )
            switchbot_device_unavailable_cancel = async_track_unavailable(
                hass, _switchbot_device_unavailable_callback, switchbot_device.address
            )

            async_fire_time_changed(
                hass, dt_util.utcnow() + timedelta(seconds=UNAVAILABLE_TRACK_SECONDS)
            )
            await hass.async_block_till_done()

            service_infos = bluetooth.async_discovered_service_info(hass)
            assert switchbot_device_went_unavailable is False
            assert wrong_device_went_unavailable is True

            # See the devices again
            inject_advertisement(hass, wrong_device, wrong_adv)
            inject_advertisement(hass, switchbot_device, switchbot_adv)
            # Cancel the callbacks
            wrong_device_unavailable_cancel()
            switchbot_device_unavailable_cancel()
            wrong_device_went_unavailable = False
            switchbot_device_went_unavailable = False

            # Verify the cancel is effective
            async_fire_time_changed(
                hass, dt_util.utcnow() + timedelta(seconds=UNAVAILABLE_TRACK_SECONDS)
            )
            await hass.async_block_till_done()
            assert switchbot_device_went_unavailable is False
            assert wrong_device_went_unavailable is False

            assert len(service_infos) == 1
            # wrong_name should not appear because bleak no longer sees it
            infos = list(service_infos)
            assert infos[0].name == "wohand"
            assert infos[0].source == SOURCE_LOCAL
            assert isinstance(infos[0].device, BLEDevice)
            assert isinstance(infos[0].advertisement, AdvertisementData)

            assert bluetooth.async_address_present(hass, "44:44:33:11:23:42") is False
            assert bluetooth.async_address_present(hass, "44:44:33:11:23:45") is True