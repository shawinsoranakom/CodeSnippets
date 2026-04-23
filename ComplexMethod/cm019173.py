async def test_devices_updated_on_refresh(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    platforms: list[str],
) -> None:
    """Test handling of devices added or deleted while event stream is down."""
    appliances: list[HomeAppliance] = (
        client.get_home_appliances.return_value.homeappliances
    )
    assert len(appliances) >= 3
    client.get_home_appliances = AsyncMock(
        return_value=ArrayOfHomeAppliances(appliances[:2]),
    )

    await async_setup_component(hass, HA_DOMAIN, {})
    await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    for appliance in appliances[:2]:
        assert device_registry.async_get_device({(DOMAIN, appliance.ha_id)})
    assert not device_registry.async_get_device({(DOMAIN, appliances[2].ha_id)})

    client.get_home_appliances = AsyncMock(
        return_value=ArrayOfHomeAppliances(appliances[1:3]),
    )
    with (
        patch("homeassistant.components.home_connect.PLATFORMS", platforms),
        patch(
            "homeassistant.components.home_connect.HomeConnectClient",
            return_value=client,
        ),
    ):
        await client.add_events([HomeConnectApiError("error.key", "error description")])
        await hass.async_block_till_done()

    assert not device_registry.async_get_device({(DOMAIN, appliances[0].ha_id)})
    for appliance in appliances[2:3]:
        assert device_registry.async_get_device({(DOMAIN, appliance.ha_id)})