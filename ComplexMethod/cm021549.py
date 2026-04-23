async def setup_and_test_unique_id(
    hass: HomeAssistant,
    platform_setup: TemplatePlatformSetup,
    style: ConfigurationStyle,
    entity_config: ConfigType | None,
    state_template: str | None = None,
) -> None:
    """Setup 2 entities with the same unique_id and verify only 1 entity is created.

    The entity_config not provide name or unique_id, those are added automatically.
    """
    if style == ConfigurationStyle.LEGACY:
        state_config = {"value_template": state_template} if state_template else {}
        entity_config = {
            "unique_id": "not-so_-unique-anymore",
            **(entity_config or {}),
            **state_config,
        }
        if platform_setup.legacy_slug is None:
            config = [
                {"name": "template_entity_1", **entity_config},
                {"name": "template_entity_2", **entity_config},
            ]
        else:
            config = {
                "template_entity_1": entity_config,
                "template_entity_2": entity_config,
            }
        await async_setup_legacy_platforms(
            hass, platform_setup.domain, platform_setup.legacy_slug, 1, config
        )
        return

    state_config = {"state": state_template} if state_template else {}
    entity_config = {
        "unique_id": "not-so_-unique-anymore",
        **(entity_config or {}),
        **state_config,
    }
    if style == ConfigurationStyle.MODERN:
        await async_setup_modern_state_format(
            hass,
            platform_setup.domain,
            1,
            [
                {"name": "template_entity_1", **entity_config},
                {"name": "template_entity_2", **entity_config},
            ],
        )
    elif style == ConfigurationStyle.TRIGGER:
        await async_setup_modern_trigger_format(
            hass,
            platform_setup.domain,
            platform_setup.trigger,
            1,
            [
                {"name": "template_entity_1", **entity_config},
                {"name": "template_entity_2", **entity_config},
            ],
        )

    assert len(hass.states.async_all(platform_setup.domain)) == 1