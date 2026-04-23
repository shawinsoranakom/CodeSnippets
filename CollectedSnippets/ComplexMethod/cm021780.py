async def test_humanify_lutron_caseta_button_event_integration_not_loaded(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test humanifying lutron_caseta_button_events when the integration fails to load."""
    hass.config.components.add("recorder")
    assert await async_setup_component(hass, "logbook", {})
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "1.1.1.1",
            CONF_KEYFILE: "",
            CONF_CERTFILE: "",
            CONF_CA_CERTS: "",
        },
        unique_id="abc",
    )
    config_entry.add_to_hass(hass)

    await async_setup_integration(hass, MockBridge, config_entry.entry_id)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    for device in device_registry.devices.values():
        if device.config_entries == {config_entry.entry_id}:
            dr_device_id = device.id
            break

    assert dr_device_id is not None
    (event1,) = mock_humanify(
        hass,
        [
            MockRow(
                LUTRON_CASETA_BUTTON_EVENT,
                {
                    ATTR_SERIAL: "68551522",
                    ATTR_DEVICE_ID: dr_device_id,
                    ATTR_TYPE: "Pico3ButtonRaiseLower",
                    ATTR_LEAP_BUTTON_NUMBER: 1,
                    ATTR_BUTTON_NUMBER: 1,
                    ATTR_DEVICE_NAME: "Pico",
                    ATTR_AREA_NAME: "Dining Room",
                    ATTR_ACTION: "press",
                },
            ),
        ],
    )

    assert event1["name"] == "Dining Room Pico"
    assert event1["domain"] == DOMAIN
    assert event1["message"] == "press stop"