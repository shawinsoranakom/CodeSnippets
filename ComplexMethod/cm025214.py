def _get_automation_component_lookup_table(
    hass: HomeAssistant,
    component_type: AutomationComponentType,
    component_descriptions: Mapping[str, Mapping[str, Any] | None],
) -> _AutomationComponentLookupTable:
    """Get a dict of automation components keyed by domain, along with the total number of components.

    Returns a cached object if available.
    """

    try:
        cache = hass.data[AUTOMATION_COMPONENT_LOOKUP_CACHE]
    except KeyError:
        cache = hass.data[AUTOMATION_COMPONENT_LOOKUP_CACHE] = {}

    if (cached := cache.get(component_type)) is not None:
        cached_descriptions, cached_lookup = cached
        if cached_descriptions is component_descriptions:
            return cached_lookup

    _LOGGER.debug(
        "Automation component lookup data for %s has no cache yet", component_type
    )

    lookup_table = _AutomationComponentLookupTable(
        domain_components={}, component_count=0
    )
    for component, description in component_descriptions.items():
        if description is None or CONF_TARGET not in description:
            _LOGGER.debug("Skipping component %s without target description", component)
            continue
        domains = _get_automation_component_domains(description[CONF_TARGET])
        lookup_data = _AutomationComponentLookupData.create(
            component, description[CONF_TARGET]
        )
        for domain in domains:
            lookup_table.domain_components.setdefault(domain, []).append(lookup_data)
        lookup_table.component_count += 1

    cache[component_type] = (component_descriptions, lookup_table)
    return lookup_table