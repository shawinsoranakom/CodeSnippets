async def async_validate_config(hass: HomeAssistant, config: ConfigType) -> ConfigType:
    """Validate config."""

    configs = []
    for key in config:
        if DOMAIN not in key:
            continue

        if key == DOMAIN or (key.startswith(DOMAIN) and len(key.split()) > 1):
            configs.append(cv.ensure_list(config[key]))

    if not configs:
        return config

    config_sections = []

    for cfg in itertools.chain(*configs):
        try:
            template_config: TemplateConfig = await async_validate_config_section(
                hass, cfg
            )
        except vol.Invalid as err:
            async_log_schema_error(err, DOMAIN, cfg, hass)
            async_notify_setup_error(hass, DOMAIN)
            continue

        legacy_warn_printed = False

        for old_key, new_key, legacy_fields in (
            (
                CONF_SENSORS,
                SENSOR_DOMAIN,
                sensor_platform.LEGACY_FIELDS,
            ),
            (
                CONF_BINARY_SENSORS,
                BINARY_SENSOR_DOMAIN,
                binary_sensor_platform.LEGACY_FIELDS,
            ),
        ):
            if old_key not in template_config:
                continue

            if not legacy_warn_printed:
                legacy_warn_printed = True
                _LOGGER.warning(
                    "The entity definition format under template: differs from the"
                    " platform "
                    "configuration format. See "
                    "https://www.home-assistant.io/integrations/template#configuration-for-trigger-based-template-sensors"
                )

            definitions = (
                list(template_config[new_key]) if new_key in template_config else []
            )
            for definition in rewrite_legacy_to_modern_configs(
                hass, new_key, template_config[old_key], legacy_fields
            ):
                create_legacy_template_issue(hass, definition, new_key)
                definitions.append(definition)
            template_config = TemplateConfig({**template_config, new_key: definitions})

        config_sections.append(template_config)

    # Create a copy of the configuration with all config for current
    # component removed and add validated config back in.
    config = config_without_domain(config, DOMAIN)
    config[DOMAIN] = config_sections

    return config