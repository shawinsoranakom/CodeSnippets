async def test_setup_component_with_webhook(
    hass: HomeAssistant, config_entry, netatmo_auth
) -> None:
    """Test setup and teardown of the netatmo component with webhook registration."""
    with selected_platforms(
        [Platform.CAMERA, Platform.CLIMATE, Platform.LIGHT, Platform.SENSOR]
    ):
        assert await hass.config_entries.async_setup(config_entry.entry_id)

        await hass.async_block_till_done()

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    await simulate_webhook(hass, webhook_id, FAKE_WEBHOOK_ACTIVATION)

    assert len(hass.states.async_all()) > 0

    webhook_id = config_entry.data[CONF_WEBHOOK_ID]
    await simulate_webhook(hass, webhook_id, FAKE_WEBHOOK_ACTIVATION)

    # Assert webhook is established successfully
    climate_entity_livingroom = "climate.livingroom"
    assert hass.states.get(climate_entity_livingroom).state == "auto"
    await simulate_webhook(hass, webhook_id, FAKE_WEBHOOK)
    assert hass.states.get(climate_entity_livingroom).state == "heat"

    for entry in hass.config_entries.async_entries("netatmo"):
        await hass.config_entries.async_remove(entry.entry_id)

    await hass.async_block_till_done()
    assert len(hass.states.async_all()) == 0
    assert len(hass.config_entries.async_entries(DOMAIN)) == 0