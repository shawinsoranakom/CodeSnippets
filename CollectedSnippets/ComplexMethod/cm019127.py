async def test_not_supported_functionality_if_not_power_setting(
    entity_registry: er.EntityRegistry,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
) -> None:
    """Test the off HVAC mode, and turn on/off is not supported when the setting is not present."""
    client.get_settings = AsyncMock(return_value=ArrayOfSettings([]))

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED

    entity = entity_registry.async_get("climate.air_conditioner")
    assert entity
    assert entity.capabilities
    assert entity.capabilities[ATTR_HVAC_MODES]
    assert HVACMode.OFF not in entity.capabilities[ATTR_HVAC_MODES]
    assert not entity.supported_features & (
        ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
    )