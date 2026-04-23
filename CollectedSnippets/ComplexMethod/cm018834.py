async def test_stale_device_removal(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mock_products: AsyncMock,
) -> None:
    """Test removal of stale devices."""

    # Setup the entry first to get a valid config_entry_id
    entry = await setup_platform(hass)

    # Create a device that should be removed (with the valid entry_id)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "stale-vin")},
        manufacturer="Tesla",
        name="Stale Vehicle",
    )

    # Verify the stale device exists
    pre_devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    stale_identifiers = {
        identifier for device in pre_devices for identifier in device.identifiers
    }
    assert (DOMAIN, "stale-vin") in stale_identifiers

    # Update products with an empty response (no devices) and reload entry
    with patch(
        "tesla_fleet_api.teslemetry.Teslemetry.products",
        return_value={"response": []},
    ):
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

        # Get updated devices after reload
        post_devices = dr.async_entries_for_config_entry(
            device_registry, entry.entry_id
        )
        post_identifiers = {
            identifier for device in post_devices for identifier in device.identifiers
        }

        # Verify the stale device has been removed
        assert (DOMAIN, "stale-vin") not in post_identifiers

        # Verify the device itself has been completely removed from the registry
        # since it had no other config entries
        updated_device = device_registry.async_get_device(
            identifiers={(DOMAIN, "stale-vin")}
        )
        assert updated_device is None