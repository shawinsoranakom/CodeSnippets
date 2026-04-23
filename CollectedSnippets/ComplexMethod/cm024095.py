async def test_bluetooth_discovery(hass: HomeAssistant) -> None:
    """Test discovery via bluetooth with a valid device."""
    wave_plus_device = AirthingsDeviceType.WAVE_PLUS
    with (
        patch_async_ble_device_from_address(WAVE_SERVICE_INFO),
        patch_airthings_ble(
            AirthingsDevice(
                manufacturer="Airthings AS",
                model=wave_plus_device,
                name="Airthings Wave Plus",
                identifier="123456",
            )
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_BLUETOOTH},
            data=WAVE_SERVICE_INFO,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    assert result["description_placeholders"] == {
        "name": "Airthings Wave Plus (2930123456)"
    }

    with patch_async_setup_entry():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"not": "empty"}
        )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Airthings Wave Plus (2930123456)"
    assert result["result"].unique_id == "cc:cc:cc:cc:cc:cc"
    assert result["data"] == {DEVICE_MODEL: wave_plus_device.value}
    assert result["result"].data == {DEVICE_MODEL: wave_plus_device.value}