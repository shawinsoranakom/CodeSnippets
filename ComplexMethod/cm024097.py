async def test_user_setup_replaces_ignored_device(hass: HomeAssistant) -> None:
    """Test the user initiated form can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="cc:cc:cc:cc:cc:cc",
        source=SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)
    wave_plus_device = AirthingsDeviceType.WAVE_PLUS
    with (
        patch(
            "homeassistant.components.airthings_ble.config_flow.async_discovered_service_info",
            return_value=[WAVE_SERVICE_INFO],
        ),
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
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None
    assert result["data_schema"] is not None
    schema = result["data_schema"].schema

    assert schema.get(CONF_ADDRESS).container == {
        "cc:cc:cc:cc:cc:cc": "Airthings Wave Plus (2930123456)"
    }

    with patch(
        "homeassistant.components.airthings_ble.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: "cc:cc:cc:cc:cc:cc"}
        )

    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Airthings Wave Plus (2930123456)"
    assert result["result"].unique_id == "cc:cc:cc:cc:cc:cc"
    assert result["data"] == {DEVICE_MODEL: wave_plus_device.value}
    assert result["result"].data == {DEVICE_MODEL: wave_plus_device.value}