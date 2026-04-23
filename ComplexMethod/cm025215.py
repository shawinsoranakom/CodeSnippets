def _async_get_automation_components_for_target(
    hass: HomeAssistant,
    component_type: AutomationComponentType,
    target_selection: ConfigType,
    expand_group: bool,
    component_descriptions: Mapping[str, Mapping[str, Any] | None],
) -> set[str]:
    """Get automation components (triggers/conditions/services) for a target.

    Returns all components that can be used on any entity that are currently part of a target.
    """
    extracted = target_helpers.async_extract_referenced_entity_ids(
        hass,
        target_helpers.TargetSelection(target_selection),
        expand_group=expand_group,
    )
    _LOGGER.debug("Extracted entities for lookup: %s", extracted)

    lookup_table = _get_automation_component_lookup_table(
        hass, component_type, component_descriptions
    )
    _LOGGER.debug(
        "Automation components per domain: %s", lookup_table.domain_components
    )

    entity_infos = entity_sources(hass)
    matched_components: set[str] = set()
    for entity_id in extracted.referenced | extracted.indirectly_referenced:
        if lookup_table.component_count == len(matched_components):
            # All automation components matched already, so we don't need to iterate further
            break

        entity_info = entity_infos.get(entity_id)
        if entity_info is None:
            _LOGGER.debug("No entity source found for %s", entity_id)
            continue

        entity_domain = entity_id.split(".")[0]
        entity_integration = entity_info["domain"]
        for domain in (entity_domain, entity_integration, None):
            if not (
                domain_component_data := lookup_table.domain_components.get(domain)
            ):
                continue
            for component_data in domain_component_data:
                if component_data.component in matched_components:
                    continue
                if component_data.matches(
                    hass, entity_id, entity_domain, entity_integration
                ):
                    matched_components.add(component_data.component)

    return matched_components