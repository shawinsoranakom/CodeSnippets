async def test_bad_config_entry_fixing(hass: HomeAssistant) -> None:
    """Test fixing/deleting config entries with bad data."""

    # Newly-added ZBT-1
    new_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="some_unique_id-9e2adbd75b8beb119fe564a0f320645d",
        data={
            "device": "/dev/serial/by-id/usb-Nabu_Casa_SkyConnect_v1.0_9e2adbd75b8beb119fe564a0f320645d-if00-port0",
            "vid": "10C4",
            "pid": "EA60",
            "serial_number": "9e2adbd75b8beb119fe564a0f320645d",
            "manufacturer": "Nabu Casa",
            "product": "SkyConnect v1.0",
            "firmware": "ezsp",
            "firmware_version": "7.4.4.0 (build 123)",
        },
        version=1,
        minor_version=3,
    )

    new_entry.add_to_hass(hass)

    # Old config entry, without firmware info
    old_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="some_unique_id-3c0ed67c628beb11b1cd64a0f320645d",
        data={
            "device": "/dev/serial/by-id/usb-Nabu_Casa_SkyConnect_v1.0_3c0ed67c628beb11b1cd64a0f320645d-if00-port0",
            "vid": "10C4",
            "pid": "EA60",
            "serial_number": "3c0ed67c628beb11b1cd64a0f320645d",
            "manufacturer": "Nabu Casa",
            "description": "SkyConnect v1.0",
        },
        version=1,
        minor_version=1,
    )

    old_entry.add_to_hass(hass)

    # Bad config entry, missing most keys
    bad_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="some_unique_id-9f6c4bba657cc9a4f0cea48bc5948562",
        data={
            "device": "/dev/serial/by-id/usb-Nabu_Casa_SkyConnect_v1.0_9f6c4bba657cc9a4f0cea48bc5948562-if00-port0",
        },
        version=1,
        minor_version=2,
    )

    bad_entry.add_to_hass(hass)

    # Bad config entry, missing most keys, but fixable since the device is present
    fixable_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="some_unique_id-4f5f3b26d59f8714a78b599690741999",
        data={
            "device": "/dev/serial/by-id/usb-Nabu_Casa_SkyConnect_v1.0_4f5f3b26d59f8714a78b599690741999-if00-port0",
        },
        version=1,
        minor_version=2,
    )

    fixable_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.homeassistant_sky_connect.async_scan_serial_ports",
        return_value=[
            USBDevice(
                device="/dev/serial/by-id/usb-Nabu_Casa_SkyConnect_v1.0_4f5f3b26d59f8714a78b599690741999-if00-port0",
                vid="10C4",
                pid="EA60",
                serial_number="4f5f3b26d59f8714a78b599690741999",
                manufacturer="Nabu Casa",
                description="SkyConnect v1.0",
            )
        ],
    ):
        await async_setup_component(hass, "homeassistant_sky_connect", {})

    assert hass.config_entries.async_get_entry(new_entry.entry_id) is not None
    assert hass.config_entries.async_get_entry(old_entry.entry_id) is not None
    assert hass.config_entries.async_get_entry(fixable_entry.entry_id) is not None

    updated_entry = hass.config_entries.async_get_entry(fixable_entry.entry_id)
    assert updated_entry is not None
    assert updated_entry.data[VID] == "10C4"
    assert updated_entry.data[PID] == "EA60"
    assert updated_entry.data[SERIAL_NUMBER] == "4f5f3b26d59f8714a78b599690741999"
    assert updated_entry.data[MANUFACTURER] == "Nabu Casa"
    assert updated_entry.data[PRODUCT] == "SkyConnect v1.0"
    assert updated_entry.data[DESCRIPTION] == "SkyConnect v1.0"

    untouched_bad_entry = hass.config_entries.async_get_entry(bad_entry.entry_id)
    assert untouched_bad_entry.minor_version == 3