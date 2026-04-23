async def test_rssi_sensor(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test the rssi sensor."""

    entry = mock_config_entry(hass)

    device = mock_melnor_device()

    with (
        patch_async_ble_device_from_address(),
        patch_melnor_device(device),
        patch_async_register_callback(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        entity_id = f"sensor.{device.name}_rssi"

        # Ensure the entity is disabled by default by checking the registry

        rssi_registry_entry = entity_registry.async_get(entity_id)

        assert rssi_registry_entry is not None
        assert rssi_registry_entry.disabled_by is not None

        # Enable the entity and assert everything else is working as expected
        entity_registry.async_update_entity(entity_id, disabled_by=None)

        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        rssi = hass.states.get(entity_id)

        assert rssi is not None
        assert (
            rssi.attributes["unit_of_measurement"] == SIGNAL_STRENGTH_DECIBELS_MILLIWATT
        )
        assert rssi.attributes["device_class"] == SensorDeviceClass.SIGNAL_STRENGTH
        assert rssi.attributes["state_class"] == SensorStateClass.MEASUREMENT