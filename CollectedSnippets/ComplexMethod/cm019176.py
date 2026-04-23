async def test_auth_error_while_updating_appliance(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
) -> None:
    """Test that the configuration entry is set to require reauth when an auth error happens."""
    entity_id = "switch.dishwasher_power"

    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get(entity_id)

    client.get_specific_appliance = AsyncMock(
        side_effect=UnauthorizedError("unauthorized")
    )

    await async_setup_component(hass, HA_DOMAIN, {})
    await hass.services.async_call(
        HA_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    flows_in_progress = hass.config_entries.flow.async_progress()
    assert len(flows_in_progress) == 1
    result = flows_in_progress[0]
    assert result["step_id"] == "reauth_confirm"
    assert result["context"]["entry_id"] == config_entry.entry_id
    assert result["context"]["source"] == "reauth"