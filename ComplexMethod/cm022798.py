async def test_config_entry_entity_id(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, target_domain: Platform
) -> None:
    """Test light switch setup from config entry with entity id."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_ENTITY_ID: "switch.abc",
            CONF_INVERT: False,
            CONF_TARGET_DOMAIN: target_domain,
        },
        title="ABC",
        version=SwitchAsXConfigFlowHandler.VERSION,
        minor_version=SwitchAsXConfigFlowHandler.MINOR_VERSION,
    )

    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert DOMAIN in hass.config.components

    state = hass.states.get(f"{target_domain}.abc")
    assert state
    assert state.state == "unavailable"
    # Name copied from config entry title
    assert state.name == "ABC"

    # Check the light is added to the entity registry
    entity_entry = entity_registry.async_get(f"{target_domain}.abc")
    assert entity_entry
    assert entity_entry.unique_id == config_entry.entry_id