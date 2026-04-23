def async_prepare_call_from_config(
    hass: HomeAssistant,
    config: ConfigType,
    variables: TemplateVarsType = None,
    validate_config: bool = False,
) -> ServiceParams:
    """Prepare to call a service based on a config hash."""
    if validate_config:
        try:
            config = cv.SERVICE_SCHEMA(config)
        except vol.Invalid as ex:
            raise HomeAssistantError(
                f"Invalid config for calling service: {ex}"
            ) from ex

    if CONF_ACTION in config:
        domain_service = config[CONF_ACTION]
    else:
        domain_service = config[CONF_SERVICE_TEMPLATE]

    if isinstance(domain_service, template.Template):
        try:
            domain_service = domain_service.async_render(variables)
            domain_service = cv.service(domain_service)
        except TemplateError as ex:
            raise HomeAssistantError(
                f"Error rendering service name template: {ex}"
            ) from ex
        except vol.Invalid as ex:
            raise HomeAssistantError(
                f"Template rendered invalid service: {domain_service}"
            ) from ex

    domain, _, service = domain_service.partition(".")

    target = {}
    if CONF_TARGET in config:
        conf = config[CONF_TARGET]
        try:
            if isinstance(conf, template.Template):
                target.update(conf.async_render(variables))
            else:
                target.update(template.render_complex(conf, variables))

            if CONF_ENTITY_ID in target:
                registry = entity_registry.async_get(hass)
                entity_ids = cv.comp_entity_ids_or_uuids(target[CONF_ENTITY_ID])
                if entity_ids not in (ENTITY_MATCH_ALL, ENTITY_MATCH_NONE):
                    entity_ids = entity_registry.async_validate_entity_ids(
                        registry, entity_ids
                    )
                target[CONF_ENTITY_ID] = entity_ids
        except TemplateError as ex:
            raise HomeAssistantError(
                f"Error rendering service target template: {ex}"
            ) from ex
        except vol.Invalid as ex:
            raise HomeAssistantError(
                f"Template rendered invalid entity IDs: {target[CONF_ENTITY_ID]}"
            ) from ex

    service_data = {}

    for conf in (CONF_SERVICE_DATA, CONF_SERVICE_DATA_TEMPLATE):
        if conf not in config:
            continue
        try:
            render = template.render_complex(config[conf], variables)
            if not isinstance(render, dict):
                raise HomeAssistantError(
                    "Error rendering data template: Result is not a Dictionary"
                )
            service_data.update(render)
        except TemplateError as ex:
            raise HomeAssistantError(f"Error rendering data template: {ex}") from ex

    if CONF_SERVICE_ENTITY_ID in config:
        if target:
            target[ATTR_ENTITY_ID] = config[CONF_SERVICE_ENTITY_ID]
        else:
            target = {ATTR_ENTITY_ID: config[CONF_SERVICE_ENTITY_ID]}

    return {
        "domain": domain,
        "service": service,
        "service_data": service_data,
        "target": target,
    }