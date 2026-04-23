async def test_switches_can_be_enabled(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Verify switches can be enabled."""
    client = create_mock_client()
    client.components = TEST_COMPONENTS
    await setup_test_config_entry(hass, hyperion_client=client)

    for component in TEST_COMPONENTS:
        name = slugify(KEY_COMPONENTID_TO_NAME[str(component["name"])])
        entity_id = TEST_SWITCH_COMPONENT_BASE_ENTITY_ID + "_" + name

        entry = entity_registry.async_get(entity_id)
        assert entry
        assert entry.disabled
        assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        entity_state = hass.states.get(entity_id)
        assert not entity_state

        with patch(
            "homeassistant.components.hyperion.client.HyperionClient",
            return_value=client,
        ):
            updated_entry = entity_registry.async_update_entity(
                entity_id, disabled_by=None
            )
            assert not updated_entry.disabled
            await hass.async_block_till_done()

            async_fire_time_changed(
                hass,
                dt_util.utcnow() + timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1),
            )
            await hass.async_block_till_done()

        entity_state = hass.states.get(entity_id)
        assert entity_state