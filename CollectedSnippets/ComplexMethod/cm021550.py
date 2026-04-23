async def setup_and_test_nested_unique_id(
    hass: HomeAssistant,
    platform_setup: TemplatePlatformSetup,
    style: ConfigurationStyle,
    entity_registry: er.EntityRegistry,
    entity_config: ConfigType | None,
    state_template: str | None = None,
) -> None:
    """Setup 2 entities with unique unique_ids in a template section that contains a unique_id.

    The test will verify that 2 entities are created where the unique_id appends the
    section unique_id to each entity unique_id.

    The entity_config should not provide name or unique_id, those are added automatically.
    """
    state_config = {"state": state_template} if state_template else {}
    entities = [
        {"name": "test_a", "unique_id": "a", **(entity_config or {}), **state_config},
        {"name": "test_b", "unique_id": "b", **(entity_config or {}), **state_config},
    ]
    extra_section_config = {"unique_id": "x"}
    if style == ConfigurationStyle.MODERN:
        await async_setup_modern_state_format(
            hass, platform_setup.domain, 1, entities, extra_section_config
        )
    elif style == ConfigurationStyle.TRIGGER:
        await async_setup_modern_trigger_format(
            hass,
            platform_setup.domain,
            platform_setup.trigger,
            1,
            entities,
            extra_section_config,
        )

    assert len(hass.states.async_all(platform_setup.domain)) == 2

    entry = entity_registry.async_get(f"{platform_setup.domain}.test_a")
    assert entry.unique_id == "x-a"

    entry = entity_registry.async_get(f"{platform_setup.domain}.test_b")
    assert entry.unique_id == "x-b"