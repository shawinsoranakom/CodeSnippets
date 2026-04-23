async def async_setup_template_platform(
    hass: HomeAssistant,
    domain: str,
    config: ConfigType,
    state_entity_cls: type[TemplateEntity],
    trigger_entity_cls: type[TriggerEntity] | None,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None,
    legacy_fields: dict[str, str] | None = None,
    legacy_key: str | None = None,
    script_options: tuple[str, ...] | None = None,
) -> None:
    """Set up the Template platform."""
    if discovery_info is None:
        # Legacy Configuration
        if legacy_fields is not None:
            if legacy_key:
                configs = rewrite_legacy_to_modern_configs(
                    hass, domain, config[legacy_key], legacy_fields
                )
            else:
                configs = [rewrite_legacy_to_modern_config(hass, config, legacy_fields)]

            for definition in configs:
                create_legacy_template_issue(hass, definition, domain)

            async_create_template_tracking_entities(
                state_entity_cls,
                async_add_entities,
                hass,
                configs,
                None,
            )
        else:
            _LOGGER.warning(
                "Template %s entities can only be configured under template:", domain
            )
        return

    # Trigger Configuration
    if "coordinator" in discovery_info:
        if trigger_entity_cls:
            entities = []
            for entity_config in discovery_info["entities"]:
                await validate_template_scripts(hass, entity_config, script_options)
                entities.append(
                    trigger_entity_cls(
                        hass, discovery_info["coordinator"], entity_config
                    )
                )
            async_add_entities(entities)
        else:
            raise PlatformNotReady(
                f"The template {domain} platform doesn't support trigger entities"
            )
        return

    # Modern Configuration
    for entity_config in discovery_info["entities"]:
        await validate_template_scripts(hass, entity_config, script_options)

    async_create_template_tracking_entities(
        state_entity_cls,
        async_add_entities,
        hass,
        discovery_info["entities"],
        discovery_info["unique_id"],
    )