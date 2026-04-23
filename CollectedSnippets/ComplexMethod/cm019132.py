async def test_connected_devices(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    appliance: HomeAppliance,
    keys_to_check: tuple,
) -> None:
    """Test that devices reconnected.

    Specifically those devices whose settings, status, etc. could
    not be obtained while disconnected and once connected, the entities are added.
    """
    get_status_original_mock = client.get_status

    def get_status_side_effect(ha_id: str):
        if ha_id == appliance.ha_id:
            raise HomeConnectApiError(
                "SDK.Error.HomeAppliance.Connection.Initialization.Failed"
            )
        return get_status_original_mock.return_value

    client.get_status = AsyncMock(side_effect=get_status_side_effect)
    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED
    client.get_status = get_status_original_mock

    device = device_registry.async_get_device(identifiers={(DOMAIN, appliance.ha_id)})
    assert device
    assert entity_registry.async_get_entity_id(
        Platform.BINARY_SENSOR,
        DOMAIN,
        f"{appliance.ha_id}-{EventKey.BSH_COMMON_APPLIANCE_CONNECTED}",
    )
    for key in keys_to_check:
        assert not entity_registry.async_get_entity_id(
            Platform.BINARY_SENSOR,
            DOMAIN,
            f"{appliance.ha_id}-{key}",
        )

    await client.add_events(
        [
            EventMessage(
                appliance.ha_id,
                EventType.CONNECTED,
                data=ArrayOfEvents([]),
            )
        ]
    )
    await hass.async_block_till_done()

    for key in (*keys_to_check, EventKey.BSH_COMMON_APPLIANCE_CONNECTED):
        assert entity_registry.async_get_entity_id(
            Platform.BINARY_SENSOR,
            DOMAIN,
            f"{appliance.ha_id}-{key}",
        )