async def setup_entity(
    hass: HomeAssistant,
    platform_setup: TemplatePlatformSetup,
    style: ConfigurationStyle,
    count: int,
    config: ConfigType,
    state_template: str | None = None,
    extra_config: ConfigType | None = None,
    attributes: ConfigType | None = None,
    extra_section_config: ConfigType | None = None,
) -> None:
    """Do setup of a template entity based on the configuration style."""
    if style == ConfigurationStyle.LEGACY:
        entity_config = {
            **({"value_template": state_template} if state_template else {}),
            **config,
            **(extra_config or {}),
            **({"attribute_templates": attributes} if attributes else {}),
        }
        # Lock and weather platforms do not use a slug.
        if platform_setup.legacy_slug is None:
            config = {"name": platform_setup.object_id, **entity_config}
        else:
            config = {platform_setup.object_id: entity_config}

        await async_setup_legacy_platforms(
            hass, platform_setup.domain, platform_setup.legacy_slug, count, config
        )
        return

    entity_config = {
        "name": platform_setup.object_id,
        **({"state": state_template} if state_template else {}),
        **config,
        **({"attributes": attributes} if attributes else {}),
        **(extra_config or {}),
    }
    if style == ConfigurationStyle.MODERN:
        await async_setup_modern_state_format(
            hass, platform_setup.domain, count, entity_config, extra_section_config
        )
    elif style == ConfigurationStyle.TRIGGER:
        await async_setup_modern_trigger_format(
            hass,
            platform_setup.domain,
            platform_setup.trigger,
            count,
            entity_config,
            extra_section_config,
        )