async def test_disabled_switches_can_be_enabled(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Verify disabled switches can be enabled."""
    client = create_mock_motioneye_client()
    await setup_mock_motioneye_config_entry(hass, client=client)

    disabled_switch_keys = [
        KEY_TEXT_OVERLAY,
        KEY_UPLOAD_ENABLED,
    ]

    for switch_key in disabled_switch_keys:
        entity_id = f"{TEST_SWITCH_ENTITY_ID_BASE}_{switch_key}"
        entry = entity_registry.async_get(entity_id)
        assert entry
        assert entry.disabled
        assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        entity_state = hass.states.get(entity_id)
        assert not entity_state

        with patch(
            "homeassistant.components.motioneye.MotionEyeClient",
            return_value=client,
        ):
            updated_entry = entity_registry.async_update_entity(
                entity_id, disabled_by=None
            )
            assert not updated_entry.disabled
            await hass.async_block_till_done()

            freezer.tick(timedelta(seconds=RELOAD_AFTER_UPDATE_DELAY + 1))
            async_fire_time_changed(hass)
            await hass.async_block_till_done()

        entity_state = hass.states.get(entity_id)
        assert entity_state