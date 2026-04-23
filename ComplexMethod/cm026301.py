def check_if_used(
    hass: HomeAssistant, entry: UFPConfigEntry, entities: dict[str, EntityRef]
) -> dict[str, EntityUsage]:
    """Check for usages of entities and return them."""

    entity_registry = er.async_get(hass)
    refs: dict[str, EntityUsage] = {
        ref: {"automations": {}, "scripts": {}} for ref in entities
    }

    for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        for ref_id, ref in entities.items():
            if (
                entity.domain == ref["platform"]
                and entity.disabled_by is None
                and ref["id"] in entity.unique_id
            ):
                entity_automations = automations_with_entity(hass, entity.entity_id)
                entity_scripts = scripts_with_entity(hass, entity.entity_id)
                if entity_automations:
                    refs[ref_id]["automations"][entity.entity_id] = entity_automations
                if entity_scripts:
                    refs[ref_id]["scripts"][entity.entity_id] = entity_scripts

    return refs