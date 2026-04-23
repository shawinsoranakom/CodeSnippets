async def test_reload(hass: HomeAssistant) -> None:
    """Verify we can reload intent config."""

    config = {"intent_script": {"NewIntent1": {"speech": {"text": "HelloWorld123"}}}}

    await async_setup_component(hass, "intent_script", config)
    await hass.async_block_till_done()

    intents = hass.data.get(intent.DATA_KEY)

    assert len(intents) == 1
    assert intents.get("NewIntent1")

    yaml_path = get_fixture_path("configuration.yaml", "intent_script")

    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    assert len(intents) == 1

    assert intents.get("NewIntent1") is None
    assert intents.get("NewIntent2")

    yaml_path = get_fixture_path("configuration_no_entry.yaml", "intent_script")

    with patch.object(hass_config, "YAML_CONFIG_FILE", yaml_path):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RELOAD,
            {},
            blocking=True,
        )
        await hass.async_block_till_done()

    # absence of intent_script from the configuration.yaml should delete all intents.
    assert len(intents) == 0
    assert intents.get("NewIntent1") is None
    assert intents.get("NewIntent2") is None