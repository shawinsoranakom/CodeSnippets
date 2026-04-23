async def _async_resolve_template_config(
    hass: HomeAssistant,
    config: ConfigType,
) -> TemplateConfig:
    """If a config item requires a blueprint, resolve that item to an actual config."""
    raw_config = None
    raw_blueprint_inputs = None

    with suppress(ValueError):  # Invalid config
        raw_config = dict(config)

    original_config = config
    config = _backward_compat_schema(config)
    if is_blueprint_instance_config(config):
        blueprints = async_get_blueprints(hass)

        blueprint_inputs = await blueprints.async_inputs_from_config(config)
        raw_blueprint_inputs = blueprint_inputs.config_with_inputs

        config = blueprint_inputs.async_substitute()

        platforms = [platform for platform in PLATFORMS if platform in config]
        if len(platforms) > 1:
            raise vol.Invalid("more than one platform defined per blueprint")
        if len(platforms) == 1:
            platform = platforms.pop()
            for prop in (CONF_NAME, CONF_UNIQUE_ID):
                if prop in config:
                    config[platform][prop] = config.pop(prop)
            # State based template entities remove CONF_VARIABLES because they pass
            # blueprint inputs to the template entities. Trigger based template entities
            # retain CONF_VARIABLES because the variables are always executed between
            # the trigger and action.
            if CONF_TRIGGERS not in config and CONF_VARIABLES in config:
                _merge_section_variables(config[platform], config.pop(CONF_VARIABLES))

        raw_config = dict(config)

    # Trigger based template entities retain CONF_VARIABLES because the variables are
    # always executed between the trigger and action.
    elif CONF_TRIGGERS not in config and CONF_VARIABLES in config:
        # State based template entities have 2 layers of variables.  Variables at the section level
        # and variables at the entity level should be merged together at the entity level.
        section_variables = config.pop(CONF_VARIABLES)
        platform_config: list[ConfigType] | ConfigType
        platforms = [platform for platform in PLATFORMS if platform in config]
        for platform in platforms:
            platform_config = config[platform]
            if platform in PLATFORMS:
                if isinstance(platform_config, dict):
                    platform_config = [platform_config]

                for entity_config in platform_config:
                    _merge_section_variables(entity_config, section_variables)

    validate_trigger_format(hass, config, original_config)
    template_config = TemplateConfig(CONFIG_SECTION_SCHEMA(config))
    template_config.raw_blueprint_inputs = raw_blueprint_inputs
    template_config.raw_config = raw_config

    return template_config